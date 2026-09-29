"""PyTorch (.pth) → ONNX (.onnx) 模型转换脚本

用法:
    python scripts/convert_to_onnx.py                    # 自动查找 weights/ 下的 .pth 文件
    python scripts/convert_to_onnx.py --input model.pth   # 指定输入文件
    python scripts/convert_to_onnx.py --input model.pth --output model.onnx

转换后自动在 weights/ 目录生成 .onnx 文件，推理速度提升 2-5 倍。
"""
import os
import sys
import argparse

# 确保项目根目录在路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
from services.ai_service import CheXNet, NUM_CLASSES, _transform


def convert_pth_to_onnx(pth_path, onnx_path=None):
    """将 PyTorch 权重文件转换为 ONNX 格式"""
    print(f"=== PyTorch → ONNX 模型转换 ===")
    print(f"输入: {pth_path}")

    # 加载 PyTorch 模型
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"设备: {device}")

    model = CheXNet(num_classes=NUM_CLASSES, pretrained=False, dropout=0.3)
    checkpoint = torch.load(pth_path, map_location=device, weights_only=False)

    state_dict = checkpoint['model_state_dict']
    # 兼容有无Dropout层的checkpoint
    has_dropout = any('classifier.1.' in k for k in state_dict.keys())
    if not has_dropout:
        new_state_dict = {}
        for k, v in state_dict.items():
            if k.startswith('densenet.classifier.0.'):
                new_key = k.replace('densenet.classifier.0.', 'densenet.classifier.1.')
                new_state_dict[new_key] = v
            else:
                new_state_dict[k] = v
        state_dict = new_state_dict

    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    # 设置输出路径
    if onnx_path is None:
        base_name = os.path.splitext(os.path.basename(pth_path))[0]
        onnx_dir = os.path.dirname(pth_path)
        onnx_path = os.path.join(onnx_dir, f"{base_name}.onnx")

    print(f"输出: {onnx_path}")

    # 导出为 ONNX（动态 batch size）
    dummy_input = torch.randn(1, 3, 224, 224, device=device)

    # Grad-CAM 需要中间层输出，导出时同时保留 features 输出
    # 但 ONNX 推理只需要最终输出，Grad-CAM 用 PyTorch 处理
    input_names = ['input']
    output_names = ['output']

    # PyTorch >= 2.6 使用新的 dynamo 导出路径，需要关闭 dynamo 以兼容旧 API
    try:
        torch.onnx.export(
            model,
            dummy_input,
            onnx_path,
            input_names=input_names,
            output_names=output_names,
            dynamic_axes={
                'input': {0: 'batch_size'},
                'output': {0: 'batch_size'},
            },
            opset_version=18,
            do_constant_folding=True,
            dynamo=False,  # 使用经典追踪模式，避免 dynamic_shapes 兼容问题
        )
    except TypeError:
        # 更旧版本的 PyTorch 不支持 dynamo 参数
        torch.onnx.export(
            model,
            dummy_input,
            onnx_path,
            input_names=input_names,
            output_names=output_names,
            dynamic_axes={
                'input': {0: 'batch_size'},
                'output': {0: 'batch_size'},
            },
            opset_version=18,
            do_constant_folding=True,
        )

    file_size_mb = os.path.getsize(onnx_path) / (1024 * 1024)
    print(f"\n[OK] ONNX conversion successful!")
    print(f"   File size: {file_size_mb:.1f} MB")
    print(f"   OP Set: 18")

    # 验证 ONNX 模型可正常加载
    try:
        import onnxruntime as ort
        sess = ort.InferenceSession(onnx_path, providers=[
            ('CUDAExecutionProvider', {'cudnn_conv_algo_search': 'ORT_TENSORRT_COMPATIBLE'}) if device.type == 'cuda' else 'CPUExecutionProvider'
        ])
        inputs = {sess.get_inputs()[0].name: dummy_input.cpu().numpy()}
        outputs = sess.run(None, inputs)
        print(f"\n[OK] ONNX validation passed! Output shape: {outputs[0].shape}")
    except ImportError:
        print("\n[WARN] onnxruntime not installed, skipping validation. Install: pip install onnxruntime-gpu (GPU) or onnxruntime (CPU)")
    except Exception as e:
        print(f"\n[WARN] ONNX validation failed: {e}")

    return onnx_path


def main():
    parser = argparse.ArgumentParser(description='PyTorch → ONNX 模型转换工具')
    parser.add_argument('--input', '-i', type=str, default=None, help='输入的 .pth/.pt 文件路径')
    parser.add_argument('--output', '-o', type=str, default=None, help='输出的 .onnx 文件路径')
    args = parser.parse_args()

    # 查找模型文件
    pth_path = args.input
    if not pth_path:
        weights_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'weights')
        if os.path.isdir(weights_dir):
            for f in sorted(os.listdir(weights_dir)):
                if f.endswith(('.pth', '.pt')):
                    pth_path = os.path.join(weights_dir, f)
                    break

    if not pth_path or not os.path.isfile(pth_path):
        # 回退到默认位置
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pth_path = os.path.join(base_dir, 'docs', 'ChestX-ray14', 'output', 'model_chestX-ray14_epochs5_81.49_v1.0.pth')

    if not os.path.isfile(pth_path):
        print(f"错误: 找不到模型文件: {pth_path}")
        sys.exit(1)

    convert_pth_to_onnx(pth_path, args.output)


if __name__ == '__main__':
    main()
