"""患者管理API"""
import time
from flask import Blueprint, request, jsonify
from extensions import db
from models.patient import Patient
from models.audit import AuditLog
from utils.auth import token_required, role_required
from utils.validators import validate_patient_no, validate_id_card

patients_bp = Blueprint('patients', __name__, url_prefix='/api/v1/patients')


@patients_bp.route('/', methods=['GET'])
@token_required
def get_patients():
    """获取患者列表（支持按 patient_no 精确查询）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '').strip()
    patient_no = request.args.get('patient_no', '').strip()  # 新增：支持精确查询

    query = Patient.query

    # 如果传入了 patient_no，精确查询
    if patient_no:
        print(f'[患者查询] 按 patient_no 精确查询: {patient_no}')
        query = query.filter(Patient.patient_no == patient_no)
    elif keyword:
        # 否则使用 keyword 模糊查询
        print(f'[患者查询] 按 keyword 模糊查询: {keyword}')
        query = query.filter(
            db.or_(Patient.name.like(f'%{keyword}%'),
                   Patient.patient_no.like(f'%{keyword}%'),
                   Patient.phone.like(f'%{keyword}%'),
                   Patient.id_card.like(f'%{keyword}%'))
        )
    else:
        print(f'[患者查询] 获取所有患者列表')

    query = query.order_by(Patient.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    print(f'[患者查询] 返回 {len(pagination.items)} 条记录')

    return jsonify({
        'code': 200,
        'data': {
            'items': [p.to_dict() for p in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
        }
    })


@patients_bp.route('/<int:patient_id>', methods=['GET'])
@token_required
@role_required('admin', 'doctor', 'nurse')  # B-12: 患者详情仅医护可见
def get_patient(patient_id):
    """获取患者详情"""
    patient = Patient.query.get_or_404(patient_id)
    return jsonify({'code': 200, 'data': patient.to_dict()})


@patients_bp.route('/', methods=['POST'])
@token_required
@role_required('admin', 'doctor', 'nurse')  # B-12: 建档仅医护可用
def create_patient():
    """创建患者（支持人脸照片上传）"""
    # 检查是否是表单数据（包含文件）
    if request.content_type and 'multipart/form-data' in request.content_type:
        patient_no = request.form.get('patient_no', '').strip()
        name = request.form.get('name', '').strip()
        face_image = request.files.get('face_image')
    else:
        data = request.get_json()
        patient_no = data.get('patient_no', '').strip()
        name = data.get('name', '').strip()
        face_image = None

    if not patient_no or not name:
        return jsonify({'code': 400, 'message': '患者编号和姓名不能为空'}), 400

    if Patient.query.filter_by(patient_no=patient_no).first():
        return jsonify({'code': 400, 'message': '患者编号已存在'}), 400

    patient = Patient(
        patient_no=patient_no,
        name=name,
        gender=request.form.get(
            'gender') if face_image else data.get('gender'),
        birth_date=request.form.get(
            'birth_date') if face_image else data.get('birth_date'),
        age=request.form.get(
            'age', type=int) if face_image else data.get('age'),
        id_card=request.form.get(
            'id_card') if face_image else data.get('id_card'),
        phone=request.form.get('phone') if face_image else data.get('phone'),
        address=request.form.get(
            'address') if face_image else data.get('address'),
        emergency_contact=request.form.get(
            'emergency_contact') if face_image else data.get('emergency_contact'),
        emergency_phone=request.form.get(
            'emergency_phone') if face_image else data.get('emergency_phone'),
        blood_type=request.form.get(
            'blood_type') if face_image else data.get('blood_type'),
        height=request.form.get(
            'height', type=float) if face_image else data.get('height'),
        weight=request.form.get(
            'weight', type=float) if face_image else data.get('weight'),
        medical_history=request.form.get(
            'medical_history') if face_image else data.get('medical_history'),
        allergy_history=request.form.get(
            'allergy_history') if face_image else data.get('allergy_history'),
        created_by=request.current_user_id,
    )

    # 处理人脸照片上传
    if face_image:
        from werkzeug.utils import secure_filename
        import os
        from config import Config

        filename = secure_filename(face_image.filename)
        ext = os.path.splitext(filename)[1]
        save_filename = f"{patient_no}_{int(time.time())}{ext}"
        upload_folder = os.path.join(Config.UPLOAD_FOLDER, 'face_images')
        os.makedirs(upload_folder, exist_ok=True)
        save_path = os.path.join(upload_folder, save_filename)
        face_image.save(save_path)

        # 转换为正斜杠路径
        patient.face_image_path = save_path.replace('\\', '/')

    db.session.add(patient)
    db.session.commit()

    _log_audit(request.current_user_id,
               'CREATE_PATIENT', 'patient', patient.id)
    return jsonify({'code': 200, 'data': patient.to_dict()})


@patients_bp.route('/<int:patient_id>', methods=['PUT'])
@token_required
@role_required('admin', 'doctor', 'nurse')  # B-12: 修改患者信息仅医护可用
def update_patient(patient_id):
    """更新患者信息（支持人脸照片上传）"""
    patient = Patient.query.get_or_404(patient_id)

    # 检查是否是表单数据（包含文件）
    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form
        face_image = request.files.get('face_image')
    else:
        data = request.get_json()
        face_image = None

    for field in ['name', 'gender', 'birth_date', 'age', 'id_card', 'phone',
                  'address', 'emergency_contact', 'emergency_phone', 'blood_type',
                  'height', 'weight', 'medical_history', 'allergy_history']:
        if field in data:
            setattr(patient, field, data[field])

    # 处理人脸照片上传（仅当没有人脸时才允许上传）
    if face_image and not patient.face_image_path:
        from werkzeug.utils import secure_filename
        import os
        from config import Config

        filename = secure_filename(face_image.filename)
        ext = os.path.splitext(filename)[1]
        save_filename = f"{patient.patient_no}_{int(time.time())}{ext}"
        upload_folder = os.path.join(Config.UPLOAD_FOLDER, 'face_images')
        os.makedirs(upload_folder, exist_ok=True)
        save_path = os.path.join(upload_folder, save_filename)
        face_image.save(save_path)

        # 转换为正斜杠路径
        patient.face_image_path = save_path.replace('\\', '/')

    db.session.commit()
    _log_audit(request.current_user_id,
               'UPDATE_PATIENT', 'patient', patient_id)
    return jsonify({'code': 200, 'data': patient.to_dict()})


@patients_bp.route('/<int:patient_id>', methods=['DELETE'])
@token_required
@role_required('admin')
def delete_patient(patient_id):
    """删除患者"""
    patient = Patient.query.get_or_404(patient_id)
    db.session.delete(patient)
    db.session.commit()
    _log_audit(request.current_user_id,
               'DELETE_PATIENT', 'patient', patient_id)
    return jsonify({'code': 200, 'message': '患者已删除'})


def _log_audit(user_id, action, resource_type, resource_id):
    try:
        log = AuditLog(user_id=user_id, action=action,
                       resource_type=resource_type, resource_id=resource_id,
                       ip_address=request.remote_addr)
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()
