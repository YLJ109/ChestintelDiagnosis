"""
接口限流中间件
防止暴力请求和DDoS攻击
基于IP地址和接口的速率限制
"""
import time
import threading
from functools import wraps
from flask import request, jsonify
from collections import defaultdict


class RateLimiter:
    """基于内存的简单限流器(生产环境建议使用Redis)"""

    def __init__(self):
        # 存储结构: {ip: {endpoint: [(timestamp, ...)]}}
        self.requests = defaultdict(lambda: defaultdict(list))
        # B-29: SocketIO 多线程环境下保护计数结构
        self._lock = threading.Lock()

        # 默认限流配置
        self.default_limits = {
            # 登录: 20次/分钟（开发环境）
            'login': {'max_requests': 20, 'window': 60},
            # 人脸识别: 10次/分钟
            'face_recognize': {'max_requests': 10, 'window': 60},
            # 一般API: 60次/分钟
            'api_general': {'max_requests': 60, 'window': 60},
            'upload': {'max_requests': 10, 'window': 60},     # 上传: 10次/分钟
        }

    def is_rate_limited(self, ip: str, endpoint: str, limit_config: dict = None) -> tuple:
        """
        检查是否超过限流阈值

        Returns:
            (is_limited: bool, remaining: int, reset_time: int)
        """
        if limit_config is None:
            # 根据endpoint选择配置
            for key, config in self.default_limits.items():
                if key in endpoint:
                    limit_config = config
                    break
            else:
                limit_config = self.default_limits['api_general']

        max_requests = limit_config['max_requests']
        window = limit_config['window']

        now = time.time()
        window_start = now - window

        with self._lock:
            # 清理过期记录
            self.requests[ip][endpoint] = [
                ts for ts in self.requests[ip][endpoint]
                if ts > window_start
            ]

            current_count = len(self.requests[ip][endpoint])

            if current_count >= max_requests:
                # 已超限
                oldest_request = min(self.requests[ip][endpoint])
                reset_time = int(oldest_request + window - now) + 1
                return True, 0, reset_time

            # 记录本次请求
            self.requests[ip][endpoint].append(now)
            remaining = max_requests - current_count - 1

        return False, remaining, window

    def cleanup(self):
        """定期清理过期数据(建议每30分钟调用一次)"""
        now = time.time()
        max_window = max(config['window']
                         for config in self.default_limits.values())
        cutoff = now - max_window

        with self._lock:
            ips_to_remove = []
            for ip in self.requests:
                endpoints_to_remove = []
                for endpoint in self.requests[ip]:
                    self.requests[ip][endpoint] = [
                        ts for ts in self.requests[ip][endpoint]
                        if ts > cutoff
                    ]
                    if not self.requests[ip][endpoint]:
                        endpoints_to_remove.append(endpoint)

                for endpoint in endpoints_to_remove:
                    del self.requests[ip][endpoint]

                if not self.requests[ip]:
                    ips_to_remove.append(ip)

            for ip in ips_to_remove:
                del self.requests[ip]


# 创建全局实例
rate_limiter = RateLimiter()


def rate_limit(limit_config: dict = None):
    """
    限流装饰器

    Usage:
        @app.route('/api/login', methods=['POST'])
        @rate_limit({'max_requests': 5, 'window': 60})
        def login():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip = request.remote_addr or 'unknown'
            endpoint = request.endpoint or request.path

            is_limited, remaining, reset_time = rate_limiter.is_rate_limited(
                ip, endpoint, limit_config
            )

            if is_limited:
                response = jsonify({
                    'success': False,
                    'message': f'请求过于频繁,请{reset_time}秒后再试',
                    'error_code': 'RATE_LIMIT_EXCEEDED'
                })
                response.status_code = 429
                response.headers['X-RateLimit-Limit'] = str(
                    limit_config['max_requests'] if limit_config else 60)
                response.headers['X-RateLimit-Remaining'] = '0'
                response.headers['X-RateLimit-Reset'] = str(reset_time)
                return response

            # 执行原函数
            response = f(*args, **kwargs)

            # 添加限流响应头
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(
                    limit_config['max_requests'] if limit_config else 60)
                response.headers['X-RateLimit-Remaining'] = str(remaining)

            return response

        return decorated_function
    return decorator


def init_rate_limiter(app):
    """初始化限流器,注册定时清理任务"""
    import threading

    def cleanup_task():
        while True:
            time.sleep(1800)  # 每30分钟清理一次
            rate_limiter.cleanup()
            print("[限流器] 已清理过期数据")

    # 启动后台清理线程
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    print("[限流器] 已启动,后台清理线程运行中")
