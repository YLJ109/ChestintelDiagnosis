"""人脸识别服务 - 基于 InsightFace + ONNX Runtime"""
import os
import sys
import threading
import numpy as np
import logging
from typing import Optional, List, Tuple

# ========== 抑制 ONNX Runtime 和 InsightFace 的日志输出 ==========
# ⚠️ 必须在导入 insightface 之前设置环境变量
os.environ['ORT_LOGGING_LEVEL'] = '3'  # 3=ERROR, 只记录错误
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # 抑制 TensorFlow 日志
os.environ['INSIGHTFACE_VERBOSE'] = '0'  # 抑制 InsightFace 详细日志

# 临时重定向 stdout/stderr 以捕获 InsightFace 的模型加载日志
_old_stdout = sys.stdout
_old_stderr = sys.stderr
sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')

try:
    import insightface
    from insightface.app import FaceAnalysis
finally:
    # 恢复标准输出
    sys.stdout.close()
    sys.stderr.close()
    sys.stdout = _old_stdout
    sys.stderr = _old_stderr

# 抑制 Python logging 日志
logging.getLogger('onnxruntime').setLevel(logging.CRITICAL)
logging.getLogger('insightface').setLevel(logging.CRITICAL)


class FaceRecognitionService:
    """人脸识别人脸识别服务（单例模式）"""

    _instance = None
    _initialized = False
    _init_lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        # 加锁双重检查，避免并发首调用重复加载 InsightFace
        with FaceRecognitionService._init_lock:
            if self._initialized:
                return

            # 初始化 InsightFace 模型（优先 GPU，自动降级 CPU）
            print("[FaceService] 正在加载人脸模型...")

            try:
                # 尝试使用 GPU，如果不可用会自动降级到 CPU
                # 使用 buffalo_s 轻量级模型，速度更快
                self.app = FaceAnalysis(
                    name='buffalo_s',  # 改为轻量级模型
                    providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
                )
                # 降低检测尺寸以提速（从 480x480 进一步降到 416x416）
                self.app.prepare(ctx_id=0, det_size=(416, 416))

                # 检测实际使用的设备
                import onnxruntime as ort
                available_providers = ort.get_available_providers()

                if 'CUDAExecutionProvider' in available_providers:
                    print("[FaceService] [OK] 推理设备: CUDA GPU (NVIDIA)")
                    print("[FaceService] [FAST] buffalo_s 模型在 GPU 上约 10-30ms/张，极速识别")
                else:
                    print("[FaceService] [INFO] 推理设备: CPU")
                    print("[FaceService] [INFO] buffalo_s 模型在 CPU 上约 50-100ms/张，快速识别")

                self._initialized = True
                print("[FaceService] 人脸模型加载成功")

            except Exception as e:
                print(f"[FaceService] [ERROR] 错误: 人脸模型加载失败: {e}")
                print("[FaceService] 将使用 CPU 模式")
                self.app = None
                self._initialized = True

    def extract_feature_from_image(self, image_path: str) -> Optional[np.ndarray]:
        """从图片文件提取人脸特征向量

        Args:
            image_path: 图片路径

        Returns:
            512 维特征向量，如果未检测到人脸则返回 None
        """
        if not self.app:
            return None

        import cv2
        img = cv2.imread(image_path)
        if img is None:
            print(f"[FaceService] 无法读取图片: {image_path}")
            return None

        return self._extract_feature(img)

    def extract_feature_from_bytes(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """从字节数据提取人脸特征向量

        Args:
            image_bytes: 图片字节数据

        Returns:
            512 维特征向量，如果未检测到人脸则返回 None
        """
        if not self.app:
            return None

        import cv2
        import numpy as np

        # 将字节转换为 numpy 数组
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            print("[FaceService] 无法解码图片数据")
            return None

        return self._extract_feature(img)

    def _extract_feature(self, img: np.ndarray) -> Optional[np.ndarray]:
        """内部方法：从图像中提取人脸特征

        Args:
            img: OpenCV 图像数组 (BGR)

        Returns:
            512 维特征向量
        """
        try:
            # 只做必要的预处理：确保是 BGR 格式
            if len(img.shape) == 2:  # 灰度图
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

            faces = self.app.get(img)

            if len(faces) == 0:
                return None

            # 选择最大的人脸
            largest_face = max(faces, key=lambda f: f.bbox[2] * f.bbox[3])

            # 获取原始特征向量（复制避免修改原始数据）
            embedding = largest_face.embedding.copy()

            # L2 归一化（InsightFace 的标准做法）
            norm = np.linalg.norm(embedding)
            if norm > 1e-10:  # 使用更严格的阈值
                embedding = embedding / norm

                # 验证归一化结果
                verify_norm = np.linalg.norm(embedding)
                if abs(verify_norm - 1.0) > 0.01:
                    print(f"[FaceService] ⚠️ 归一化异常: 范数={verify_norm:.6f}")

            return embedding

        except Exception as e:
            print(f"[FaceService] 特征提取失败: {e}")
            return None

    def _validate_embedding(self, embedding: np.ndarray) -> bool:
        """验证特征向量质量

        Args:
            embedding: 512 维特征向量

        Returns:
            是否有效
        """
        # 检查维度
        if embedding.shape != (512,):
            print(f"[FaceService] ❌ 特征维度错误: {embedding.shape}")
            return False

        # 检查是否为 NaN 或 Inf
        if np.any(np.isnan(embedding)) or np.any(np.isinf(embedding)):
            print("[FaceService] ❌ 特征向量包含 NaN 或 Inf")
            return False

        # 检查范数(归一化后应该接近 1.0)
        norm = np.linalg.norm(embedding)
        if abs(norm - 1.0) > 0.1:
            print(f"[FaceService] ⚠️ 特征向量范数异常: {norm:.4f}")
            return False

        # 检查特征分布(不应该全为 0 或全相同)
        if np.all(embedding == 0) or np.std(embedding) < 0.01:
            print("[FaceService] ❌ 特征向量退化(全零或方差过小)")
            return False

        return True

    @staticmethod
    def _normalize_embedding(embedding: np.ndarray) -> np.ndarray:
        """对特征向量进行 L2 归一化

        Args:
            embedding: 原始特征向量

        Returns:
            归一化后的特征向量
        """
        # 确保是 numpy 数组
        if not isinstance(embedding, np.ndarray):
            embedding = np.array(embedding, dtype=np.float32)

        # L2 归一化
        norm = np.linalg.norm(embedding)
        if norm > 1e-10:
            embedding = embedding / norm

            # 验证归一化结果
            verify_norm = np.linalg.norm(embedding)
            if abs(verify_norm - 1.0) > 0.01:
                print(f"[FaceService] ⚠️ 归一化异常: 范数={verify_norm:.6f}")
        else:
            print("[FaceService] ⚠️ 特征向量范数接近 0，无法归一化")

        return embedding

    def recognize_from_frame(self, frame: np.ndarray) -> Optional[Tuple[np.ndarray, dict]]:
        """从视频帧检测并提取人脸特征

        Args:
            frame: OpenCV 视频帧 (BGR)

        Returns:
            (特征向量, 人脸信息字典) 或 None
            人脸信息字典包含: bbox, kps, face_image (base64)
        """
        import time
        t_start = time.time()

        if not self.app:
            print(f"[FaceService] ❌ app 未加载，无法识别")
            return None

        try:
            t_start = time.time()
            faces = self.app.get(frame)
            elapsed = (time.time() - t_start) * 1000

            if len(faces) == 0:
                return None

            # 选择最大的人脸（最靠近摄像头）
            largest_face = max(faces, key=lambda f: f.bbox[2] * f.bbox[3])

            # 提取人脸截图
            face_image_base64 = self._extract_face_image(
                frame, largest_face.bbox)

            face_info = {
                'bbox': largest_face.bbox.tolist(),  # 边界框 [x1, y1, x2, y2]
                'kps': largest_face.kps.tolist() if largest_face.kps is not None else None,  # 关键点
                'face_image': face_image_base64  # 人脸截图 (base64)
            }

            total_elapsed = (time.time() - t_start) * 1000
            return largest_face.embedding, face_info

        except Exception as e:
            print(f"[FaceService] 人脸检测失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _extract_face_image(self, frame: np.ndarray, bbox: np.ndarray) -> Optional[str]:
        """提取人脸区域截图并转换为 base64

        Args:
            frame: 原始图像 (BGR)
            bbox: 人脸边界框 [x1, y1, x2, y2]

        Returns:
            base64 编码的人脸截图 (JPEG)
        """
        import base64
        import cv2

        try:
            x1, y1, x2, y2 = map(int, bbox)

            # 裁剪人脸区域，添加一些边距
            h, w = frame.shape[:2]
            margin_x = int((x2 - x1) * 0.2)
            margin_y = int((y2 - y1) * 0.3)

            x1 = max(0, x1 - margin_x)
            y1 = max(0, y1 - margin_y)
            x2 = min(w, x2 + margin_x)
            y2 = min(h, y2 + margin_y)

            face_roi = frame[y1:y2, x1:x2]

            # 编码为 JPEG
            _, buffer = cv2.imencode(
                '.jpg', face_roi, [cv2.IMWRITE_JPEG_QUALITY, 85])

            # 转换为 base64
            face_base64 = base64.b64encode(buffer).decode('utf-8')

            return face_base64

        except Exception as e:
            print(f"[FaceService] 提取人脸截图失败: {e}")
            return None

    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算两个向量的余弦相似度

        Args:
            vec1: 特征向量 1
            vec2: 特征向量 2

        Returns:
            余弦相似度 (0-1)，越大越相似
        """
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = np.dot(vec1, vec2) / (norm1 * norm2)
        return float(similarity)

    @staticmethod
    def match_face(query_embedding: np.ndarray,
                   stored_embeddings: List[Tuple[int, np.ndarray]],
                   threshold: float = 0.6) -> Optional[Tuple[int, float]]:
        """匹配人脸特征（使用向量化计算加速）

        Args:
            query_embedding: 查询的特征向量
            stored_embeddings: 存储的特征向量列表 [(patient_id, embedding), ...]
            threshold: 相似度阈值（默认 0.6）

        Returns:
            (patient_id, similarity) 或 None
        """
        import time
        t_start = time.time()

        if not stored_embeddings:
            return None

        # 向量化计算：将所有特征向量堆叠成矩阵
        patient_ids = []
        embedding_matrix = []

        for patient_id, emb in stored_embeddings:
            patient_ids.append(patient_id)
            embedding_matrix.append(emb)

        # 转换为 numpy 数组
        embedding_matrix = np.array(embedding_matrix)  # (N, 512)
        query_norm = np.linalg.norm(query_embedding)

        if query_norm == 0:
            return None

        # 归一化查询向量
        query_normalized = query_embedding / query_norm

        # 计算所有存储向量的范数
        norms = np.linalg.norm(embedding_matrix, axis=1)  # (N,)

        # 避免除以 0
        norms[norms == 0] = 1e-10

        # 归一化存储向量
        embedding_normalized = embedding_matrix / \
            norms[:, np.newaxis]  # (N, 512)

        # 一次性计算所有余弦相似度（矩阵乘法）
        similarities = np.dot(embedding_normalized, query_normalized)  # (N,)

        # 找到最大相似度
        best_idx = np.argmax(similarities)
        best_similarity = float(similarities[best_idx])
        best_match_id = patient_ids[best_idx]

        print(
            f"[FaceService] 向量化匹配耗时: {(time.time() - t_start) * 1000:.2f}ms, 共 {len(patient_ids)} 个患者")

        # 阈值判断
        if best_similarity >= threshold:
            return best_match_id, best_similarity

        return None


# 全局单例
face_service = FaceRecognitionService()
