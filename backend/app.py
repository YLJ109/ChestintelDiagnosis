"""Flask应用入口 - 胸影智诊V3.0"""
import warnings
from api import all_blueprints
from extensions import db, cors, socketio, limiter
from config import get_config
import logging
from flask import Flask, send_from_directory
from flask_cors import CORS
import os
import sys

# 禁用 Python 用户站点，避免从全局目录加载包
os.environ['PYTHONNOUSERSITE'] = '1'

# 忽略 gevent 的 PyTorch 弃用警告
warnings.filterwarnings('ignore', message='.*torch.distributed.reduce_op.*')


# 抑制 ONNX Runtime 的所有日志（包括 CUDA 加载错误）
logging.getLogger('onnxruntime').setLevel(logging.CRITICAL)  # 只显示致命错误

# 也可以完全禁用 ONNX Runtime 日志
# 0=Verbose, 1=Info, 2=Warning, 3=Error, 4=Fatal
os.environ['ORT_LOGGING_LEVEL'] = '3'


def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    config_class = get_config()
    app.config.from_object(config_class)

    # 确保数据目录存在
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)

    # 初始化扩展
    db.init_app(app)

    # B-30: CORS 白名单 —— 优先取 CORS_ORIGINS 环境变量（逗号分隔）；
    # 未配置时默认放行本机与局域网私有网段（方便移动端联调），生产环境务必显式配置
    cors_origins_env = os.getenv('CORS_ORIGINS', '')
    if cors_origins_env:
        cors_origins = [o.strip() for o in cors_origins.split(',') if o.strip()]
    else:
        cors_origins = [
            r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
            r"^https?://192\.168\.\d{1,3}\.\d{1,3}(:\d+)?$",
            r"^https?://10\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?$",
            r"^https?://172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}(:\d+)?$",
        ]
    cors.init_app(app, resources={r"/*": {"origins": cors_origins}})

    socketio.init_app(app)
    limiter.init_app(app)

    # 初始化自定义限流器
    from utils.rate_limiter import init_rate_limiter
    init_rate_limiter(app)

    # 注册蓝图
    for bp in all_blueprints:
        app.register_blueprint(bp)

    # 静态文件服务（上传的图片、热力图等）
    upload_folder = app.config['UPLOAD_FOLDER']

    @app.route('/static/images/<path:filename>')
    def serve_image(filename):
        return send_from_directory(os.path.join(upload_folder, 'images'), filename)

    @app.route('/static/heatmaps/<path:filename>')
    def serve_heatmap(filename):
        return send_from_directory(os.path.join(upload_folder, 'heatmaps'), filename)

    @app.route('/static/reports/<path:filename>')
    def serve_report(filename):
        return send_from_directory(os.path.join(upload_folder, 'reports'), filename)

    # 健康检查
    @app.route('/api/v1/health', methods=['GET'])
    def health_check():
        return {'code': 200, 'message': 'ok', 'data': {'status': 'healthy'}}

    # 全局错误处理
    @app.errorhandler(404)
    def not_found(e):
        return {'code': 404, 'message': '资源不存在'}, 404

    @app.errorhandler(500)
    def internal_error(e):
        import traceback
        error_trace = traceback.format_exc()
        print(f"[服务器错误] {error_trace}")
        return {'code': 500, 'message': '服务器内部错误', 'error': str(e) if app.debug else None}, 500

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return {
            'code': 429,
            'message': '请求过于频繁，请稍后再试',
            'error_code': 'RATE_LIMIT_EXCEEDED'
        }, 429

    @app.errorhandler(Exception)
    def handle_exception(e):
        """捕获所有未处理的异常"""
        import traceback
        error_trace = traceback.format_exc()
        print(f"[未处理异常] {error_trace}")

        # 记录到审计日志（如果有用户上下文）
        try:
            from flask import request
            from models.audit import AuditLog
            audit_log = AuditLog(
                user_id=None,
                action='EXCEPTION',
                resource=request.path if request else 'unknown',
                details=f'{type(e).__name__}: {str(e)}',
                ip_address=request.remote_addr if request else None
            )
            db.session.add(audit_log)
            db.session.commit()
        except:
            pass  # 忽略审计日志记录失败

        return {
            'code': 500,
            'message': '服务器内部错误',
            'error': str(e) if app.debug else None,
            'type': type(e).__name__
        }, 500

    # S-03: 请求上下文异常时回滚未提交事务，避免脏数据残留
    @app.teardown_appcontext
    def rollback_on_error(exc=None):
        if exc is not None:
            try:
                db.session.rollback()
            except Exception:
                pass

    # 应用启动后初始化数据库表并加载AI模型
    with app.app_context():
        # 幂等建表（含新增的 revoked_tokens 黑名单表）
        db.create_all()
        from services.ai_service import load_model
        try:
            load_model()
        except Exception as e:
            print(f"[启动] AI模型加载失败: {e}")
            print("[启动] 系统将以无模型模式启动，诊断功能不可用")

    return app


if __name__ == '__main__':
    app = create_app()
    print("=" * 50)
    print("  胸影智诊V3.0 - AI智能辅助诊断系统")
    print("  访问地址: http://localhost:5000")
    print("=" * 50)
    # debug=True: 开发模式（代码修改自动重启）；生产务必关闭，避免 Werkzeug 调试器 RCE
    # 由环境变量 FLASK_DEBUG=1 显式开启，默认关闭
    socketio.run(app, host='0.0.0.0', port=5000,
                 debug=os.getenv('FLASK_DEBUG', '0') == '1')
