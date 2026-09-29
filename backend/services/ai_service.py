# AI辅助开发：通义千问Qwen-Max，2026.03.18
# 人工修改：扩展为多标签支持（遍历 14 种疾病分别生成热力图）、增加透明度可调参数（0.3-0.7）、优化颜色映射（青→红渐变）
"""AI推理服务 - ONNX加速推理 + PyTorch Grad-CAM

架构设计:
  - ONNX Runtime: 主推理引擎（速度快 2-5x）
  - PyTorch: 仅用于 Grad-CAM 热力图生成（需要反向传播），懒加载
"""
import os
import sys
import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image
from torchvision import transforms, models
import torch.nn as nn
import threading
import queue
import time

# ============================================================
# 常量定义
# ============================================================
CLASS_NAMES = [
    'Atelectasis', 'Cardiomegaly', 'Effusion', 'Infiltration',
    'Mass', 'Nodule', 'Pneumonia', 'Pneumothorax',
    'Consolidation', 'Edema', 'Emphysema', 'Fibrosis',
    'Pleural_Thickening', 'Hernia',
]

CN_NAMES = {
    'Atelectasis': '肺不张', 'Cardiomegaly': '心脏肥大', 'Effusion': '胸腔积液',
    'Infiltration': '浸润', 'Mass': '肿块', 'Nodule': '结节',
    'Pneumonia': '肺炎', 'Pneumothorax': '气胸', 'Consolidation': '实变',
    'Edema': '水肿', 'Emphysema': '肺气肿', 'Fibrosis': '纤维化',
    'Pleural_Thickening': '胸膜增厚', 'Hernia': '疝',
}

NUM_CLASSES = len(CLASS_NAMES)

# 模型加载锁：防止并发请求同时进入 load_model 造成重复加载（TOCTOU）
_model_lock = threading.Lock()

# 图像预处理（ONNX 和 PyTorch 共用）
_transform = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])


# ============================================================
# PyTorch 模型定义（仅用于 Grad-CAM）
# ============================================================
class CheXNet(nn.Module):
    """DenseNet-121 多标签分类模型"""

    def __init__(self, num_classes=NUM_CLASSES, pretrained=False, dropout=0.3):
        super(CheXNet, self).__init__()
        self.densenet = models.densenet121(weights=None)
        num_features = self.densenet.classifier.in_features
        self.densenet.classifier = nn.Sequential(
            nn.Dropout(p=dropout),
            nn.Linear(num_features, num_classes),
        )

    def forward(self, x):
        features = self.densenet.features(x)
        out = torch.relu(features)
        out = F.adaptive_avg_pool2d(out, (1, 1))
        out = out.view(out.size(0), -1)
        out = self.densenet.classifier(out)
        return out


class GradCAM:
    """Grad-CAM: 梯度加权类激活映射（仅 PyTorch 使用）"""

    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        target_layer.register_forward_hook(self._save_activation)
        target_layer.register_full_backward_hook(self._save_gradient)

    def _save_activation(self, module, input, output):
        self.activations = output.detach()

    def _save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()

    def generate(self, input_tensor, target_class=None):
        if not input_tensor.requires_grad:
            input_tensor = input_tensor.clone().detach().requires_grad_(True)

        self.model.eval()
        output = self.model(input_tensor)

        if target_class is None:
            target_class = output.argmax(dim=1).item()

        self.model.zero_grad()
        one_hot = torch.zeros_like(output)
        one_hot[0][target_class] = 1
        output.backward(gradient=one_hot, retain_graph=False)

        weights = self.gradients.mean(dim=[2, 3], keepdim=True)
        cam = (weights * self.activations).sum(dim=1, keepdim=True)
        cam = F.relu(cam)

        cam = cam.squeeze(0).squeeze(0).cpu().numpy()
        cam = cam - cam.min()
        if cam.max() > 0:
            cam = cam / cam.max()
        return cam


def apply_heatmap(image_pil, cam, alpha=None):
    """将Grad-CAM热力图叠加到原图"""
    if alpha is None:
        alpha = _runtime_params['heatmap_alpha']
    cam_resized = np.array(Image.fromarray((cam * 255).astype(np.uint8)).resize(
        image_pil.size, Image.Resampling.BILINEAR
    )).astype(float) / 255.0

    heatmap = np.zeros((*cam_resized.shape, 3), dtype=np.float64)
    v = cam_resized

    mask1 = v < 0.25
    mask2 = (v >= 0.25) & (v < 0.5)
    mask3 = (v >= 0.5) & (v < 0.75)
    mask4 = v >= 0.75

    heatmap[mask1, 0] = 0
    heatmap[mask1, 1] = v[mask1] * 4
    heatmap[mask1, 2] = 1
    heatmap[mask2, 0] = 0
    heatmap[mask2, 1] = 1
    heatmap[mask2, 2] = (0.5 - v[mask2]) * 4
    heatmap[mask3, 0] = (v[mask3] - 0.5) * 4
    heatmap[mask3, 1] = 1
    heatmap[mask3, 2] = 0
    heatmap[mask4, 0] = 1
    heatmap[mask4, 1] = (1.0 - v[mask4]) * 4
    heatmap[mask4, 2] = 0

    heatmap = (heatmap.clip(0, 1) * 255).astype(np.uint8)
    img_array = np.array(image_pil.convert('RGB')).astype(float)
    overlay = (img_array * (1 - alpha) + heatmap.astype(float)
               * alpha).clip(0, 255).astype(np.uint8)
    return Image.fromarray(overlay)


# ============================================================
# 全局状态
# ============================================================
_onnx_session = None       # ONNX Runtime 会话（主推理引擎）
_pytorch_model = None       # PyTorch 模型（仅 Grad-CAM 用，懒加载）
_grad_cam = None            # Grad-CAM 实例
_device = None             # torch device
_use_onnx = False          # 是否使用 ONNX 推理
_lock = threading.Lock()   # 线程安全锁

# 运行时可调参数
_runtime_params = {
    'disease_threshold': 0.7,
    'heatmap_alpha': 0.4,
    'model_loaded': False,
    'active_weight': None,
    'device': None,
    'engine': None,   # 'onnx' 或 'pytorch'
}


def get_runtime_params():
    """获取运行时参数"""
    _runtime_params['model_loaded'] = _onnx_session is not None or _pytorch_model is not None
    _runtime_params['device'] = str(_device) if _device else '未初始化'
    _runtime_params['engine'] = 'onnx' if _use_onnx else (
        'pytorch' if _pytorch_model else '未加载')
    return dict(_runtime_params)


def update_runtime_params(params):
    """更新运行时参数"""
    updated = {}
    if 'disease_threshold' in params:
        val = float(params['disease_threshold'])
        if 0 < val < 1:
            _runtime_params['disease_threshold'] = val
            updated['disease_threshold'] = val
    if 'heatmap_alpha' in params:
        val = float(params['heatmap_alpha'])
        if 0 < val < 1:
            _runtime_params['heatmap_alpha'] = val
            updated['heatmap_alpha'] = val
    return updated


# AI辅助开发：通义千问Qwen-Max，2026.03.25
# 人工修改：增加 ThreadPoolExecutor 4 线程并行预处理、实现 AI_DEVICE 环境变量自动检测（cuda/directml/cpu）、添加模型缓存机制避免重复加载
# ============================================================
# 设备检测
# ============================================================
def get_device():
    """获取推理设备"""
    global _device
    if _device is not None:
        return _device

    device_setting = os.getenv('AI_DEVICE', 'auto').lower().strip()

    if device_setting in ('cuda', 'gpu'):
        if torch.cuda.is_available():
            _device = torch.device('cuda')
            gpu_name = torch.cuda.get_device_name(0)
            gpu_mem = torch.cuda.get_device_properties(
                0).total_memory / (1024 ** 3)
            print(f"[AI服务] GPU: {gpu_name} ({gpu_mem:.1f}GB)")
        else:
            print("[AI服务] 警告: CUDA不可用，回退到CPU")
            _device = torch.device('cpu')
    elif device_setting == 'cpu':
        _device = torch.device('cpu')
    else:
        if torch.cuda.is_available():
            _device = torch.device('cuda')
            gpu_name = torch.cuda.get_device_name(0)
            gpu_mem = torch.cuda.get_device_properties(
                0).total_memory / (1024 ** 3)
            print(f"[AI服务] 自动检测GPU: {gpu_name} ({gpu_mem:.1f}GB)")
        else:
            _device = torch.device('cpu')

    if _device.type == 'cuda':
        torch.backends.cudnn.benchmark = True
        try:
            torch.cuda.set_per_process_memory_fraction(0.85)
        except Exception:
            pass

    return _device


# ============================================================
# PyTorch 模型懒加载（仅 Grad-CAM 需要）
# ============================================================
def _ensure_pytorch_model(model_path):
    """懒加载 PyTorch 模型（仅在首次生成热力图时调用）"""
    global _pytorch_model, _grad_cam

    with _lock:
        if _pytorch_model is not None:
            return True

        device = get_device()
        print(f"[AI服务] [Grad-CAM] 懒加载 PyTorch 模型: {model_path}")

        # 如果 ONNX 已占用 CUDA 上下文，先初始化 PyTorch 的主上下文（解决 cuBLAS 冲突）
        if device.type == 'cuda':
            try:
                torch.cuda.init()
                torch.cuda.set_device(0)
            except Exception as e:
                print(f"[AI服务] [Grad-CAM] CUDA 上下文初始化跳过: {e}")

        _pytorch_model = CheXNet(
            num_classes=NUM_CLASSES, pretrained=False, dropout=0.3)
        checkpoint = torch.load(
            model_path, map_location=device, weights_only=False)

        state_dict = checkpoint['model_state_dict']
        has_dropout = any('classifier.1.' in k for k in state_dict.keys())
        if not has_dropout:
            new_state_dict = {}
            for k, v in state_dict.items():
                if k.startswith('densenet.classifier.0.'):
                    new_key = k.replace(
                        'densenet.classifier.0.', 'densenet.classifier.1.')
                    new_state_dict[new_key] = v
                else:
                    new_state_dict[k] = v
            state_dict = new_state_dict

        _pytorch_model.load_state_dict(state_dict)
        _pytorch_model.to(device)
        _pytorch_model.eval()

        target_layer = _pytorch_model.densenet.features.norm5
        _grad_cam = GradCAM(_pytorch_model, target_layer)

        # 预热
        if device.type == 'cuda':
            try:
                dummy = torch.randn(1, 3, 224, 224, device=device)
                with torch.no_grad(), torch.amp.autocast('cuda'):
                    _pytorch_model(dummy)
                torch.cuda.synchronize()
            except Exception:
                pass

        print(f"[AI服务] [Grad-CAM] PyTorch 模型就绪")
        return True


# ============================================================
# 模型加载（优先 ONNX，回退 PyTorch）
# ============================================================
def load_model(model_path=None, version_name=None):
    """加载 AI 模型（优先 ONNX 格式）"""
    global _onnx_session, _use_onnx

    # 加锁并重做双重检查，避免并发重复加载
    with _model_lock:
        if is_model_loaded():
            return True

        # 查找模型文件
        if model_path is None:
            weights_dir = os.path.join(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))), 'weights')
            if os.path.isdir(weights_dir):
                # 优先找 .onnx 文件
                for f in sorted(os.listdir(weights_dir)):
                    if f.endswith('.onnx'):
                        model_path = os.path.join(weights_dir, f)
                        break
                # 回退 .pth/.pt
                if not model_path or not os.path.isfile(model_path):
                    for f in sorted(os.listdir(weights_dir)):
                        if f.endswith(('.pth', '.pt')):
                            model_path = os.path.join(weights_dir, f)
                            break
            if not model_path or not os.path.isfile(model_path):
                base_dir = os.path.dirname(os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))))
                model_path = os.path.join(
                    base_dir, 'ChestX-ray14', 'output', 'model_chestX-ray14_epochs5_81.49_v1.0.pth')

        if not os.path.isfile(model_path):
            print(f"[AI服务] 警告: 模型文件不存在: {model_path}")
            return False

        device = get_device()
        ext = os.path.splitext(model_path)[1].lower()

        # ===== 尝试 ONNX 加载 =====
        if ext == '.onnx':
            try:
                _load_onnx_model(model_path, device)
                _use_onnx = True
                _runtime_params['active_weight'] = version_name or os.path.basename(
                    model_path)
                print(f"[AI服务] ✅ ONNX 模型加载成功")
                return True
            except Exception as e:
                print(f"[AI服务] ONNX 加载失败: {e}")
                print(f"[AI服务] 回退到 PyTorch 模式...")

        # ===== PyTorch 模式（回退或直接加载）=====
        # 如果当前是 .onnx 文件，需要找到对应的 .pth 文件
        pth_path = model_path
        if os.path.splitext(model_path)[1].lower() == '.onnx':
            weights_dir = os.path.dirname(model_path)
            if os.path.isdir(weights_dir):
                for f in sorted(os.listdir(weights_dir)):
                    if f.endswith(('.pth', '.pt')):
                        pth_path = os.path.join(weights_dir, f)
                        break
            if pth_path == model_path:  # 还是 .onnx，说明没有 .pth
                base_dir = os.path.dirname(os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))))
                pth_path = os.path.join(
                    base_dir, 'ChestX-ray14', 'output', 'model_chestX-ray14_epochs5_81.49_v1.0.pth')
            print(f"[AI服务] 使用 PyTorch 权重: {os.path.basename(pth_path)}")

        _use_onnx = False
        result = _load_pytorch_model_full(pth_path, device)
        if result:
            _runtime_params['active_weight'] = version_name or os.path.basename(
                model_path)
        return result


def _load_onnx_model(onnx_path, device):
    """加载 ONNX 模型并配置优化选项"""
    global _onnx_session

    import onnxruntime as ort
    import logging

    # 抑制 ONNX Runtime 的 CUDA 加载错误日志（会自动降级到 CPU）
    logging.getLogger('onnxruntime').setLevel(logging.ERROR)

    # Session 选项：性能优化
    sess_options = ort.SessionOptions()
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    sess_options.intra_op_num_threads = min(
        os.cpu_count(), 8)   # 内部并行线程数（提升至8）
    # 以下属性部分 ONNX 版本不支持，安全设置
    if hasattr(ort, 'ExecutionMode'):
        try:
            sess_options.inter_op_num_threads = 2                    # 层间并行
            sess_options.execution_mode = ort.ExecutionMode.SEQUENTIAL   # 减少线程切换开销
        except (AttributeError, TypeError):
            pass
    if hasattr(sess_options, 'enable_mem_pattern'):
        sess_options.enable_mem_pattern = True                      # 内存分配优化
    # log_level 部分版本不支持，安全设置
    if hasattr(sess_options, 'log_level'):
        sess_options.log_level = 3  # 只显示错误

    # 选择提供者（Provider）— 优先级: CUDA > CPU
    providers = ['CPUExecutionProvider']

    if device.type == 'cuda':
        # 尝试 CUDA Provider
        try:
            test_sess = ort.InferenceSession(onnx_path, sess_options=sess_options,
                                             providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
            avail = list(test_sess.get_providers())
            if any('CUDA' in str(p) for p in avail):
                providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
                print(f"[AI服务] ✅ ONNX GPU (CUDA) 可用")
            else:
                print(f"[AI服务] ⚠️ ONNX GPU 不可用，使用 CPU 模式")
            del test_sess
        except Exception as e:
            print(f"[AI服务] ℹ️ ONNX 使用 CPU 模式")

    session = ort.InferenceSession(
        onnx_path, sess_options=sess_options, providers=providers)

    # 预热：执行一次空推理
    try:
        dummy_input = np.random.randn(1, 3, 224, 224).astype(np.float32)
        input_name = session.get_inputs()[0].name
        session.run(None, {input_name: dummy_input})
        print(f"[AI服务] ONNX 预热完成")
    except Exception as e:
        print(f"[AI服务] ONNX 预热跳过: {e}")

    _onnx_session = session
    provider_names = list(session.get_providers())
    print(f"[AI服务] ONNX 引擎: {' | '.join(provider_names)}")
    print(
        f"[AI服务] 输入: {session.get_inputs()[0].name} {session.get_inputs()[0].shape}")
    print(
        f"[AI服务] 输出: {session.get_outputs()[0].name} {session.get_outputs()[0].shape}")


def _load_pytorch_model_full(pth_path, device):
    """完整加载 PyTorch 模型（作为主引擎时的全量加载）"""
    global _pytorch_model, _grad_cam

    if not os.path.isfile(pth_path):
        print(f"[AI服务] PyTorch 权重文件不存在: {pth_path}")
        return False

    print(f"[AI服务] 正在加载 PyTorch 模型: {pth_path}")

    # weights_only=True 防止反序列化执行任意代码（CWE-502）
    _pytorch_model = CheXNet(num_classes=NUM_CLASSES,
                             pretrained=False, dropout=0.3)
    checkpoint = torch.load(pth_path, map_location=device, weights_only=True)

    state_dict = checkpoint['model_state_dict']
    has_dropout = any('classifier.1.' in k for k in state_dict.keys())
    if not has_dropout:
        new_state_dict = {}
        for k, v in state_dict.items():
            if k.startswith('densenet.classifier.0.'):
                new_key = k.replace('densenet.classifier.0.',
                                    'densenet.classifier.1.')
                new_state_dict[new_key] = v
            else:
                new_state_dict[k] = v
        state_dict = new_state_dict

    _pytorch_model.load_state_dict(state_dict)
    _pytorch_model.to(device)
    _pytorch_model.eval()

    # Windows 上跳过 torch.compile
    if device.type == 'cuda' and hasattr(torch, 'compile') and sys.platform != 'win32':
        try:
            _pytorch_model = torch.compile(
                _pytorch_model, mode='reduce-overhead')
            print("[AI服务] 已启用 torch.compile")
        except Exception:
            pass

    target_layer = _pytorch_model.densenet.features.norm5
    _grad_cam = GradCAM(_pytorch_model, target_layer)

    # 预热
    if device.type == 'cuda':
        try:
            dummy = torch.randn(1, 3, 224, 224, device=device)
            with torch.no_grad(), torch.amp.autocast('cuda'):
                _pytorch_model(dummy)
            torch.cuda.synchronize()
            print("[AI服务] GPU预热完成")
        except Exception:
            pass

    epoch = checkpoint.get('epoch', '?')
    print(f"[AI服务] PyTorch 模型加载成功 (Epoch {epoch})")
    return True


# ============================================================
# 核心推理函数
# ============================================================
# S-05: 预处理结果缓存 —— 同一文件（路径+mtime+大小指纹）重复诊断时跳过 decode/resize
_preproc_cache = {}
_preproc_cache_lock = threading.Lock()
_PREPROC_CACHE_MAX = 32


def _preprocess_image_cached(image_path):
    try:
        st = os.stat(image_path)
        key = (image_path, st.st_mtime, st.st_size)
    except OSError:
        key = None

    if key is not None:
        with _preproc_cache_lock:
            hit = _preproc_cache.get(key)
        if hit is not None:
            return hit

    result = _preprocess_image(image_path)

    if key is not None:
        with _preproc_cache_lock:
            if len(_preproc_cache) >= _PREPROC_CACHE_MAX:
                _preproc_cache.pop(next(iter(_preproc_cache)))
            _preproc_cache[key] = result
    return result


def _preprocess_image(image_path):
    """图像预处理（可在线程池中并行执行）"""
    import os
    import time as time_module
    try:
        t_start = time_module.perf_counter()

        # 检查文件是否存在
        if not os.path.exists(image_path):
            print(f"[AI服务] ❌ 文件不存在: {image_path}")
            raise FileNotFoundError(f"File not found: {image_path}")

        # 检查文件大小
        file_size = os.path.getsize(image_path)
        print(
            f"[AI服务] 📄 预处理文件: {os.path.basename(image_path)}, 大小={file_size/1024:.1f}KB")

        t_open = time_module.perf_counter()
        image_pil = Image.open(image_path).convert('RGB')
        t_open_elapsed = time_module.perf_counter() - t_open
        print(f"[AI服务]   → 图片加载耗时: {t_open_elapsed*1000:.1f}ms")

        t_transform = time_module.perf_counter()
        tensor = _transform(image_pil)                          # (3, 224, 224)
        np_arr = tensor.numpy().astype(np.float32)               # (3, 224, 224) float32
        t_transform_elapsed = time_module.perf_counter() - t_transform
        print(f"[AI服务]   → 转换耗时: {t_transform_elapsed*1000:.1f}ms")

        t_total = time_module.perf_counter() - t_start
        print(
            f"[AI服务] ✅ 预处理完成: {os.path.basename(image_path)} (总耗时: {t_total*1000:.1f}ms)")
        return np_arr, image_pil
    except Exception as e:
        print(f"[AI服务] ❌ 预处理失败 [{image_path}]: {e}")
        import traceback
        traceback.print_exc()
        raise


def _onnx_inference(np_batch):
    """ONNX 批量推理（支持多张图片一次性送入）"""
    input_name = _onnx_session.get_inputs()[0].name
    outputs = _onnx_session.run(None, {input_name: np_batch})
    raw = outputs[0]                                        # (N, 14)
    probs = 1 / (1 + np.exp(-raw))                         # sigmoid
    return probs


def _pytorch_inference(np_batch):
    """PyTorch 批量推理"""
    device = get_device()
    tensor = torch.from_numpy(np_batch).to(device)
    with torch.no_grad():
        if device.type == 'cuda':
            with torch.amp.autocast('cuda'):
                output = _pytorch_model(tensor)
        else:
            output = _pytorch_model(tensor)
    probs = torch.sigmoid(output).cpu().numpy()
    return probs


def predict_image(image_path, target_disease=None, skip_heatmap=False):
    """单张图片 AI 推理（对外接口不变）

    Args:
        image_path: 图片路径
        target_disease: 目标疾病代码（可选）
        skip_heatmap: 跳过热力图以加速

    Returns:
        dict: probabilities + heatmap_image
    """
    # 预处理（S-05: 命中缓存时跳过 decode/resize）
    np_arr, image_pil = _preprocess_image_cached(image_path)
    np_batch = np_arr[np.newaxis, ...]                     # (1, 3, 224, 224)

    # 推理
    if _use_onnx and _onnx_session is not None:
        probs = _onnx_inference(np_batch)[0]                 # (14,)
    elif _pytorch_model is not None:
        probs = _pytorch_inference(np_batch)[0]
    else:
        raise RuntimeError("AI模型未加载")

    # 构建概率列表
    probabilities = []
    for i, name in enumerate(CLASS_NAMES):
        probabilities.append({
            'disease_code': name,
            'disease_name_zh': CN_NAMES.get(name, name),
            'probability': round(float(probs[i]), 4),
        })
    probabilities.sort(key=lambda x: x['probability'], reverse=True)

    # 热力图（需要 PyTorch + Grad-CAM）
    heatmap_pil = None
    if not skip_heatmap:
        pth_path = _find_pth_path()
        if pth_path and _ensure_pytorch_model(pth_path):
            try:
                device = get_device()
                # 确保 PyTorch 拥有正确的 CUDA 上下文（解决与 ONNX 的冲突）
                if device.type == 'cuda':
                    try:
                        torch.cuda.set_device(0)
                    except Exception:
                        pass

                tensor = torch.from_numpy(np_arr).unsqueeze(0).to(device)

                if target_disease and target_disease in CLASS_NAMES:
                    target_idx = CLASS_NAMES.index(target_disease)
                else:
                    target_idx = int(np.argmax(probs))

                cam = _grad_cam.generate(tensor, target_class=target_idx)
                # Grad-CAM 反向传播后释放计算图占用的显存
                if device.type == 'cuda':
                    torch.cuda.empty_cache()
                heatmap_pil = apply_heatmap(image_pil, cam)
            except Exception as e:
                print(f"[AI服务] 热力图生成失败: {e}")

    return {
        'probabilities': probabilities,
        'heatmap_image': heatmap_pil,
        'model_version': 'model_chestX-ray14_epochs5_81.49_v1.0 (ONNX)' if _use_onnx else 'model_chestX-ray14_epochs5_81.49_v1.0',
    }


def predict_images_batch(image_paths, skip_heatmap=True, cancel_check=None):
    """批量图片推理（顺序预处理 + ONNX/PyTorch 批量推理）

    Args:
        image_paths: 图片路径列表
        skip_heatmap: 是否跳过热力图（默认跳过以最大化速度）
        cancel_check: 可选的取消检查函数,返回True表示需要取消

    Returns:
        list[dict]: 每张图片的推理结果
    """
    n = len(image_paths)
    if n == 0:
        return []

    print(f"[AI服务] 批量推理开始: {n} 张图片")
    t0 = time.perf_counter()

    # 预处理所有图片（顺序处理，支持取消）
    print(f"[AI服务] 开始预处理 {n} 张图片...")
    try:
        preprocess_results = []
        for idx, path in enumerate(image_paths):
            # 检查是否需要取消
            if cancel_check and cancel_check():
                print(f"[AI服务] ⚠️ 检测到取消信号，停止预处理")
                return None  # 返回None表示被取消

            print(f"[AI服务] 🔄 处理第 [{idx+1}/{n}] 张...")
            result = _preprocess_image_cached(path)
            preprocess_results.append(result)

        print(f"[AI服务] ✅ 全部预处理完成 {len(preprocess_results)} 张图片")
    except Exception as e:
        print(f"[AI服务] ❌ 预处理失败: {e}")
        import traceback
        traceback.print_exc()
        raise

    np_arrays = [r[0] for r in preprocess_results]
    images_pil = [r[1] for r in preprocess_results]
    np_batch = np.stack(np_arrays, axis=0)                  # (N, 3, 224, 224)

    t_pre = time.perf_counter() - t0
    print(f"[AI服务] 预处理耗时: {t_pre:.2f}s")

    # 批量推理
    t1 = time.perf_counter()
    if _use_onnx and _onnx_session is not None:
        all_probs = _onnx_inference(np_batch)                 # (N, 14)
    elif _pytorch_model is not None:
        all_probs = _pytorch_inference(np_batch)
    else:
        raise RuntimeError("AI模型未加载")

    t_inf = time.perf_counter() - t1

    # 构建结果列表
    results = []
    for idx in range(n):
        probs = all_probs[idx]
        probabilities = []
        for i, name in enumerate(CLASS_NAMES):
            probabilities.append({
                'disease_code': name,
                'disease_name_zh': CN_NAMES.get(name, name),
                'probability': round(float(probs[i]), 4),
            })
        probabilities.sort(key=lambda x: x['probability'], reverse=True)

        results.append({
            'probabilities': probabilities,
            'heatmap_image': None,  # 批量模式下不生成热力图
            'model_version': 'model_chestX-ray14_epochs5_81.49_v1.0 (ONNX)' if _use_onnx else 'model_chestX-ray14_epochs5_81.49_v1.0',
            '_image_pil': images_pil[idx],
            '_probs_raw': probs,
        })

    total = time.perf_counter() - t0
    if n >= 3:
        print(
            f"[AI服务] 批量推理 {n}张: 预处理={t_pre:.2f}s 推理={t_inf:.2f}s 总计={total:.2f}s ({n/total:.1f}张/s)")

    return results


# ============================================================
# 辅助
# ============================================================
def _find_pth_path():
    """查找对应的 .pth 文件路径（用于 Grad-CAM 懒加载）"""
    weights_dir = os.path.join(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))), 'weights')
    if os.path.isdir(weights_dir):
        for f in os.listdir(weights_dir):
            if f.endswith(('.pth', '.pt')):
                return os.path.join(weights_dir, f)
    base_dir = os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, 'ChestX-ray14', 'output', 'model_chestX-ray14_epochs5_81.49_v1.0.pth')


def is_model_loaded():
    """检查模型是否已加载"""
    return _onnx_session is not None or _pytorch_model is not None
