"""用户管理API"""
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from extensions import db
from models.user import User
from models.settings import UserPreference
from models.audit import AuditLog
from utils.auth import token_required, role_required

users_bp = Blueprint('users', __name__, url_prefix='/api/v1/users')


@users_bp.route('/', methods=['GET'])
@token_required
@role_required('admin')
def get_users():
    """获取用户列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    role = request.args.get('role')
    status = request.args.get('status')
    keyword = request.args.get('keyword', '').strip()

    query = User.query
    if role:
        query = query.filter_by(role=role)
    if status:
        query = query.filter_by(status=status)
    if keyword:
        query = query.filter(
            db.or_(User.username.like(f'%{keyword}%'),
                   User.real_name.like(f'%{keyword}%'))
        )

    # 按角色排序：管理员优先，然后医生，最后护士
    # 使用 CASE WHEN 实现自定义排序
    from sqlalchemy import case
    role_order = case(
        (User.role == 'admin', 1),
        (User.role == 'doctor', 2),
        (User.role == 'nurse', 3),
        else_=4
    )
    query = query.order_by(role_order, User.id.asc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'code': 200,
        'data': {
            'items': [u.to_dict() for u in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
        }
    })


@users_bp.route('/<int:user_id>', methods=['GET'])
@token_required
@role_required('admin')
def get_user(user_id):
    """获取单个用户详情"""
    user = User.query.get_or_404(user_id)
    return jsonify({'code': 200, 'data': user.to_dict()})


@users_bp.route('/<int:user_id>', methods=['PUT'])
@token_required
@role_required('admin')
def update_user(user_id):
    """更新用户信息"""
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if 'real_name' in data:
        user.real_name = data['real_name']
    if 'role' in data and data['role'] in ('admin', 'doctor', 'nurse'):
        user.role = data['role']
    if 'department' in data:
        user.department = data['department']
    if 'license_number' in data:
        user.license_number = data['license_number']
    if 'email' in data:
        user.email = data['email']
    if 'phone' in data:
        user.phone = data['phone']
    if 'status' in data and data['status'] in ('active', 'disabled'):
        user.status = data['status']

    db.session.commit()
    _log_audit(request.current_user_id, 'UPDATE_USER', 'user', user_id)
    return jsonify({'code': 200, 'data': user.to_dict()})


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@token_required
@role_required('admin')
def delete_user(user_id):
    """删除用户"""
    user = User.query.get_or_404(user_id)
    if user.id == request.current_user_id:
        return jsonify({'code': 400, 'message': '不能删除自己'}), 400
    user.status = 'disabled'
    db.session.commit()
    _log_audit(request.current_user_id, 'DELETE_USER', 'user', user_id)
    return jsonify({'code': 200, 'message': '用户已禁用'})


@users_bp.route('/<int:user_id>/reset-password', methods=['POST'])
@token_required
@role_required('admin')
def reset_password(user_id):
    """重置用户密码"""
    user = User.query.get_or_404(user_id)
    data = request.get_json(silent=True) or {}
    new_password = data.get('new_password')
    if not new_password or len(new_password) < 6:
        return jsonify({'code': 400, 'message': '新密码不能为空且至少 6 位'}), 400
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    _log_audit(request.current_user_id, 'RESET_PASSWORD', 'user', user_id)
    return jsonify({'code': 200, 'message': '密码已重置'})


@users_bp.route('/<int:user_id>/preferences', methods=['PUT'])
@token_required
def update_preferences(user_id):
    """更新用户偏好"""
    if request.current_user_role != 'admin' and request.current_user_id != user_id:
        return jsonify({'code': 403, 'message': '权限不足'}), 403

    pref = UserPreference.query.filter_by(user_id=user_id).first()
    if not pref:
        pref = UserPreference(user_id=user_id)
        db.session.add(pref)

    data = request.get_json()
    if 'theme' in data and data['theme'] in ('light', 'dark'):
        pref.theme = data['theme']
    if 'language' in data:
        pref.language = data['language']
    if 'notification_enabled' in data:
        pref.notification_enabled = data['notification_enabled']
    if 'default_llm_model' in data:
        pref.default_llm_model = data['default_llm_model']

    db.session.commit()
    return jsonify({'code': 200, 'data': pref.to_dict()})


def _log_audit(user_id, action, resource_type, resource_id):
    """记录审计日志"""
    from models.audit import AuditLog
    try:
        log = AuditLog(user_id=user_id, action=action,
                       resource_type=resource_type, resource_id=resource_id,
                       ip_address=request.remote_addr)
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()
