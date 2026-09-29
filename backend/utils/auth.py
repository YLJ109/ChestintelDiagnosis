"""JWT认证工具"""
import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, current_app
from models.user import User
from models.patient import Patient


def generate_token(user_id, role, username):
    """生成JWT Token"""
    now = datetime.now(timezone.utc)  # ⚠️ 关键修复：使用UTC时间
    payload = {
        'user_id': user_id,
        'role': role,
        'username': username,
        'exp': now + timedelta(seconds=current_app.config['JWT_ACCESS_TOKEN_EXPIRES']),
        'iat': now,
    }
    token = jwt.encode(
        payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
    return token


def decode_token(token):
    """解码JWT Token"""
    try:
        # ⚠️ 安全：禁止打印任何密钥片段到日志（避免密钥泄露）
        secret_key = current_app.config['JWT_SECRET_KEY']
        payload = jwt.decode(
            token, secret_key, algorithms=['HS256'])

        # ⚠️ 完全禁用成功日志，避免刷屏
        # if current_app.debug:
        #     print(f'[Token验证] ✅ 成功, user_id={payload.get("user_id")}, role={payload.get("role")}')

        return payload
    except jwt.ExpiredSignatureError:
        print(f'[Token验证] ❌ Token已过期')
        return None
    except jwt.InvalidTokenError as e:
        print(f'[Token验证] ❌ Token无效: {str(e)}')
        return None


def token_required(f):
    """Token验证装饰器（支持医护人员和患者）"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'code': 401, 'message': '缺少认证Token'}), 401

        payload = decode_token(token)
        if not payload:
            return jsonify({'code': 401, 'message': 'Token无效或已过期'}), 401

        role = payload.get('role', '')
        user_id = payload['user_id']

        if role == 'patient':
            # 患者登录：从Patient表查询
            patient = Patient.query.get(user_id)
            if not patient:
                return jsonify({'code': 401, 'message': '患者信息不存在'}), 401
            request.current_user = patient
            request.current_user_id = user_id
            request.current_user_role = 'patient'
            request.current_username = payload.get('username', '')
        else:
            # 医护人员：从User表查询
            user = User.query.get(user_id)
            if not user or user.status != 'active':
                return jsonify({'code': 401, 'message': '用户不存在或已被禁用'}), 401
            request.current_user = user
            request.current_user_id = user_id
            request.current_user_role = role
            request.current_username = user.username

        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    """角色验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, 'current_user_role'):
                return jsonify({'code': 401, 'message': '请先登录'}), 401
            if request.current_user_role not in roles:
                return jsonify({'code': 403, 'message': '权限不足'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
