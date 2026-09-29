"""认证API - 登录、注册、获取用户信息"""
import os
import io
import base64
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models.user import User
from models.patient import Patient
from models.settings import UserPreference, LoginSession
from models.audit import AuditLog
from utils.auth import generate_token, token_required, role_required
from utils.rate_limiter import rate_limit
import qrcode

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')


@auth_bp.route('/login', methods=['POST'])
@rate_limit({'max_requests': 5, 'window': 60})  # 5次/分钟
def login():
    """用户登录"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空'}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        # 记录失败日志
        _log_audit(None, username, 'LOGIN_FAILED',
                   None, None, request.remote_addr)
        return jsonify({'code': 401, 'message': '用户名或密码错误'}), 401

    if user.status != 'active':
        return jsonify({'code': 403, 'message': '账号已被禁用，请联系管理员'}), 403

    # 生成Token
    token = generate_token(user.id, user.role, user.username)

    # 更新登录时间
    user.last_login_at = datetime.now()
    db.session.commit()

    # 创建登录会话
    session = LoginSession(
        user_id=user.id,
        session_token=token,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', ''),
        # ⚠️ P0-7: 使用 datetime.now() 保持时区一致
        expires_at=datetime.now(),
    )
    db.session.add(session)
    db.session.commit()

    # 记录审计日志
    _log_audit(user.id, user.username, 'LOGIN',
               None, None, request.remote_addr)

    # 获取用户主题偏好
    pref = UserPreference.query.filter_by(user_id=user.id).first()

    return jsonify({
        'code': 200,
        'data': {
            'token': token,
            'user': user.to_dict(),
            'theme': pref.theme if pref else 'light',
        }
    })


@auth_bp.route('/staff-face-login', methods=['POST'])
def staff_face_login():
    """医护人员刷脸登录（无需密码）

    Request:
        - user_id: 用户ID
        - username: 用户名
        - real_name: 真实姓名
        - role: 角色
        - department: 部门
        - face_image: 人脸截图 (base64)
        - similarity: 相似度

    Response:
        - code: 200
        - data: token, user
    """
    data = request.get_json()

    user_id = data.get('user_id')
    username = data.get('username')
    real_name = data.get('real_name')
    role = data.get('role')
    department = data.get('department')

    if not user_id or not username:
        return jsonify({'code': 400, 'message': '缺少用户信息'}), 400

    try:
        # 查找用户
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404

        if user.status != 'active':
            return jsonify({'code': 403, 'message': '账号已被禁用，请联系管理员'}), 403

        # 生成 Token
        token = generate_token(user.id, user.role, user.username)

        # 记录审计日志
        _log_audit(
            user_id=user.id,
            username=user.username,
            action='LOGIN_FACE',
            resource_type=None,
            resource_id=None,
            ip=request.remote_addr
        )

        # 返回用户信息和 token
        return jsonify({
            'code': 200,
            'message': '刷脸登录成功',
            'data': {
                'token': token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'real_name': user.real_name,
                    'role': user.role,
                    'department': user.department,
                    'email': user.email,
                    'avatar_url': user.avatar_url
                },
                'theme': 'dark'  # 医护人员使用深色主题
            }
        })

    except Exception as e:
        print(f"[Auth] 刷脸登录失败: {e}")
        return jsonify({'code': 500, 'message': f'登录失败: {str(e)}'}), 500


@auth_bp.route('/patient-login', methods=['POST'])
def patient_login():
    """患者登录（患者编号 / 二维码扫码）"""
    data = request.get_json()
    patient_no = data.get('patient_no', '').strip()
    # patient_no / qrcode
    login_method = data.get('login_method', 'patient_no')

    if not patient_no:
        return jsonify({'code': 400, 'message': '请输入患者编号'}), 400

    patient = Patient.query.filter_by(patient_no=patient_no).first()
    if not patient:
        return jsonify({'code': 404, 'message': '未找到该患者编号，请确认后重试'}), 404

    # 生成患者Token（role=patient）
    token = generate_token(
        user_id=patient.id,
        role='patient',
        username=f"patient_{patient.patient_no}"
    )

    # 记录审计日志
    _log_audit(
        None, f"PATIENT:{patient.patient_no}", 'PATIENT_LOGIN',
        'patient', patient.id, request.remote_addr
    )

    return jsonify({
        'code': 200,
        'data': {
            'token': token,
            'user': {
                'id': patient.id,
                'username': f"patient_{patient.patient_no}",
                'real_name': patient.name,
                'role': 'patient',
                'patient_id': patient.id,  # 添加 patient_id 用于前端显示
                'patient_no': patient.patient_no,
                'name': patient.name,
                'gender': patient.gender,
                'age': patient.age,
                'phone': patient.phone,
            },
            'login_method': login_method,
        }
    })


@auth_bp.route('/patient-qrcode/<int:patient_id>', methods=['GET'])
@token_required
def generate_patient_qrcode(patient_id):
    """生成患者专属二维码（Base64图片）"""
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'code': 404, 'message': '患者不存在'}), 404

    # 二维码内容格式：PATIENT_QRCODE:{patient_no}
    qrcode_content = f"PATIENT_QRCODE:{patient.patient_no}"

    # 生成二维码
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(qrcode_content)
    qr.make(fit=True)

    # 生成图片
    img = qr.make_image(fill_color="black", back_color="white")

    # 转换为Base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return jsonify({
        'code': 200,
        'data': {
            'patient_id': patient.id,
            'patient_no': patient.patient_no,
            'patient_name': patient.name,
            'qrcode_base64': f"data:image/png;base64,{img_str}",
            'qrcode_content': qrcode_content,
        }
    })


@auth_bp.route('/staff-qrcode/<int:user_id>', methods=['GET'])
@token_required
def generate_staff_qrcode(user_id):
    """生成医护人员专属二维码（Base64图片）"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404

    # 二维码内容格式：STAFF_QRCODE:{username}
    qrcode_content = f"STAFF_QRCODE:{user.username}"

    # 生成二维码
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(qrcode_content)
    qr.make(fit=True)

    # 生成图片
    img = qr.make_image(fill_color="black", back_color="white")

    # 转换为Base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return jsonify({
        'code': 200,
        'data': {
            'user_id': user.id,
            'username': user.username,
            'real_name': user.real_name,
            'role': user.role,
            'qrcode_base64': f"data:image/png;base64,{img_str}",
            'qrcode_content': qrcode_content,
        }
    })


@auth_bp.route('/register', methods=['POST'])
@token_required
@role_required('admin')
def register():
    """管理员注册新用户"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    real_name = data.get('real_name', '').strip()
    role = data.get('role', 'nurse')

    if not all([username, password, real_name]):
        return jsonify({'code': 400, 'message': '用户名、密码和真实姓名不能为空'}), 400

    if role not in ('admin', 'doctor', 'nurse'):
        return jsonify({'code': 400, 'message': '无效的角色类型'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'code': 400, 'message': '用户名已存在'}), 400

    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        real_name=real_name,
        role=role,
    )
    db.session.add(user)
    db.session.commit()

    _log_audit(
        request.current_user_id, request.current_username,
        'USER_CREATE', 'admin', user.id, request.remote_addr
    )

    return jsonify({
        'code': 200,
        'message': '用户创建成功',
        'data': {'id': user.id, 'username': user.username}
    })


@auth_bp.route('/patient-register', methods=['POST'])
def patient_register():
    """患者自助注册（无需登录）"""
    data = request.get_json()

    name = data.get('name', '').strip()
    gender = data.get('gender', 'male')
    age = data.get('age')
    phone = data.get('phone', '').strip()
    patient_no = data.get('patient_no', '').strip()

    # 验证必填字段
    if not name:
        return jsonify({'code': 400, 'message': '姓名不能为空'}), 400

    if not patient_no:
        return jsonify({'code': 400, 'message': '患者编号不能为空'}), 400

    # 检查患者编号是否已存在
    if Patient.query.filter_by(patient_no=patient_no).first():
        return jsonify({'code': 400, 'message': '该患者编号已被注册'}), 400

    # 验证性别
    if gender not in ['male', 'female']:
        return jsonify({'code': 400, 'message': '性别必须为 male 或 female'}), 400

    # 验证年龄
    if age is not None and (not isinstance(age, int) or age < 0 or age > 150):
        return jsonify({'code': 400, 'message': '年龄必须在 0-150 之间'}), 400

    try:
        # 创建患者记录
        patient = Patient(
            patient_no=patient_no,
            name=name,
            gender=gender,
            age=age,
            phone=phone,
        )
        db.session.add(patient)
        db.session.commit()

        # 记录审计日志
        _log_audit(
            None, f"PATIENT:{patient_no}", 'PATIENT_REGISTER',
            'patient', patient.id, request.remote_addr
        )

        return jsonify({
            'code': 200,
            'message': '注册成功',
            'data': {
                'id': patient.id,
                'patient_no': patient.patient_no,
                'name': patient.name,
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"[PatientRegister] 注册失败: {e}")
        return jsonify({'code': 500, 'message': f'注册失败: {str(e)}'}), 500


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user():
    """获取当前登录用户信息"""
    user = request.current_user
    pref = UserPreference.query.filter_by(user_id=user.id).first()
    return jsonify({
        'code': 200,
        'data': {
            **user.to_dict(),
            'theme': pref.theme if pref else 'light',
        }
    })


@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password():
    """修改密码"""
    data = request.get_json()
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    user = request.current_user
    if not check_password_hash(user.password_hash, old_password):
        return jsonify({'code': 400, 'message': '原密码错误'}), 400

    user.password_hash = generate_password_hash(new_password)
    db.session.commit()

    _log_audit(user.id, user.username, 'CHANGE_PASSWORD',
               'user', user.id, request.remote_addr)
    return jsonify({'code': 200, 'message': '密码修改成功'})


@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """用户登出（B-22: 将当前 Token 写入黑名单，立即失效）"""
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.split(' ', 1)[1] if auth_header.startswith('Bearer ') else None
    if token:
        from utils.auth import decode_token
        from models.revoked_token import RevokedToken
        payload = decode_token(token)
        if payload and payload.get('jti'):
            try:
                expires_at = datetime.fromtimestamp(
                    payload['exp'], tz=timezone.utc
                ).replace(tzinfo=None) if payload.get('exp') else None
                db.session.add(RevokedToken(
                    jti=payload['jti'],
                    user_id=request.current_user_id,
                    expires_at=expires_at,
                ))
                db.session.commit()
            except Exception:
                db.session.rollback()  # 黑名单写入失败不阻断登出
    _log_audit(request.current_user_id, request.current_user.username,
               'LOGOUT', None, None, request.remote_addr)
    return jsonify({'code': 200, 'message': '已登出'})


@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile():
    """获取当前用户详细信息"""
    user = request.current_user
    pref = UserPreference.query.filter_by(user_id=user.id).first()
    return jsonify({
        'code': 200,
        'data': {
            **user.to_dict(),
            'theme': pref.theme if pref else 'light',
        }
    })


@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile():
    """更新当前用户个人信息"""
    user = request.current_user
    data = request.get_json()

    if 'real_name' in data:
        user.real_name = data['real_name']
    if 'email' in data:
        user.email = data['email']
    if 'phone' in data:
        user.phone = data['phone']
    if 'department' in data:
        user.department = data['department']
    if 'license_number' in data:
        user.license_number = data['license_number']
    if 'avatar_url' in data:
        user.avatar_url = data['avatar_url']

    db.session.commit()

    _log_audit(user.id, user.username, 'UPDATE_PROFILE',
               'user', user.id, request.remote_addr)
    return jsonify({'code': 200, 'message': '个人信息更新成功', 'data': user.to_dict()})


def _log_audit(user_id, username, action, resource_type, resource_id, ip):
    """记录审计日志"""
    try:
        log = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip,
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()
