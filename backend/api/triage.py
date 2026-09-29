"""智能分诊API"""
import json
from flask import Blueprint, request, jsonify
from extensions import db
from models.triage import TriageRecord
from models.patient import Patient
from models.audit import AuditLog
from utils.auth import token_required, role_required
from services.llm_service import triage_analyze

triage_bp = Blueprint('triage', __name__, url_prefix='/api/v1/triage')


@triage_bp.route('/analyze', methods=['POST'])
@token_required
def analyze():
    """智能分诊分析"""
    data = request.get_json()
    symptoms = data.get('symptoms', [])
    symptom_duration = data.get('symptom_duration', '')
    severity = data.get('severity', 'mild')
    vital_signs = data.get('vital_signs')
    patient_id = data.get('patient_id')

    if not symptoms:
        return jsonify({'code': 400, 'message': '请提供症状信息'}), 400

    # B-15: 患者角色只能为自己分诊，忽略请求体中的 patient_id
    if request.current_user_role == 'patient':
        patient_id = request.current_user_id

    # AI分诊
    result = triage_analyze(symptoms, severity, vital_signs)

    # 保存分诊记录
    record = TriageRecord(
        patient_id=patient_id,
        symptoms=json.dumps(symptoms, ensure_ascii=False) if isinstance(symptoms, list) else symptoms,
        symptom_duration=symptom_duration,
        severity=severity,
        vital_signs=json.dumps(vital_signs, ensure_ascii=False) if vital_signs else None,
        ai_triage_result=json.dumps(result, ensure_ascii=False),
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({
        'code': 200,
        'data': {
            'record_id': record.id,
            **result,
        }
    })


@triage_bp.route('/records', methods=['GET'])
@token_required
def get_triage_records():
    """获取分诊记录列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = TriageRecord.query
    # B-15: 患者只能查看自己的分诊记录
    if request.current_user_role == 'patient':
        query = query.filter_by(patient_id=request.current_user_id)

    query = query.order_by(TriageRecord.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'code': 200,
        'data': {
            'items': [r.to_dict() for r in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
        }
    })


@triage_bp.route('/<int:record_id>/confirm', methods=['POST'])
@token_required
@role_required('admin', 'doctor')  # B-15: 确认分诊仅医生可用
def confirm_triage(record_id):
    """医生确认分诊结果"""
    record = TriageRecord.query.get_or_404(record_id)
    data = request.get_json()

    record.doctor_confirmed = True
    record.confirmed_by = request.current_user_id

    # 医生可调整分诊结果
    if data.get('adjusted_result'):
        import json
        result = json.loads(record.ai_triage_result) if record.ai_triage_result else {}
        result.update(data['adjusted_result'])
        record.ai_triage_result = json.dumps(result, ensure_ascii=False)

    db.session.commit()
    return jsonify({'code': 200, 'data': record.to_dict()})
