"""Flask应用配置管理"""
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))), '.env'))


class Config:
    """基础配置"""
    # ⚠️ P0-8: JWT密钥长度至少32字节，满足SHA256安全要求（RFC 7518 Section 3.2）
    SECRET_KEY = os.getenv(
        'SECRET_KEY', 'aixray-default-secret-key-change-in-production')
    JWT_SECRET_KEY = os.getenv(
        'JWT_SECRET_KEY', 'aixray-jwt-secret-key-must-be-at-least-32-bytes-long!')
    JWT_ACCESS_TOKEN_EXPIRES = 2592000  # 30天（秒）

    # SQLite数据库
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "data", "aixray.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 文件上传
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB（模型权重文件较大）
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'dcm', 'dicom'}

    # AI模型
    MODEL_WEIGHTS_DIR = os.path.join(BASE_DIR, 'model_files')
    DEFAULT_MODEL_PATH = os.path.join(
        os.path.dirname(BASE_DIR),
        'docs', 'ChestX-ray14', 'output', 'model_chestX-ray14_epochs5_81.49_v1.0.pth'
    )

    # LLM配置
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_API_BASE = os.getenv(
        'OPENAI_API_BASE', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
    LLM_ENCRYPTION_KEY = os.getenv(
        'LLM_ENCRYPTION_KEY', 'aixray-llm-encryption-secret-key-2026')

    # 诊断阈值
    DISEASE_THRESHOLD = 0.7

    # 热力图
    HEATMAP_ALPHA = 0.4

    # AI推理设备 (cuda/cpu/auto)，auto=自动检测
    AI_DEVICE = os.getenv('AI_DEVICE', 'auto')

    # 审计日志保留天数
    AUDIT_RETENTION_DAYS = 180


class DevelopmentConfig(Config):
    DEBUG = True
    FLASK_ENV = 'development'


class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = 'production'


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}


def get_config():
    env = os.getenv('FLASK_ENV', 'development')
    config_cls = config_map.get(env, DevelopmentConfig)
    # B-07: 生产环境强制拒绝默认密钥
    if env == 'production':
        insecure = [k for k in ('SECRET_KEY', 'JWT_SECRET_KEY', 'LLM_ENCRYPTION_KEY')
                    if getattr(config_cls, k, '').startswith('aixray-')]
        if insecure:
            raise RuntimeError(
                f'生产环境禁止使用默认密钥，请通过环境变量/\.env 设置: {", ".join(insecure)}')
    return config_cls
