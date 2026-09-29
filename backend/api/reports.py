"""报告管理API"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from extensions import db
from models.diagnosis import Diagnosis
from models.report import Report
from models.audit import AuditLog
from utils.auth import token_required, role_required

reports_bp = Blueprint('reports', __name__, url_prefix='/api/v1/reports')


@reports_bp.route('/pending', methods=['GET'])
@token_required
@role_required('admin', 'doctor')
def get_pending_reports():
    """获取待审核报告列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Diagnosis.query.filter_by(report_status='pending_review')\
        .order_by(Diagnosis.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    from models.patient import Patient
    from models.diagnosis import DiseaseProbability
    items = []
    for d in pagination.items:
        patient = Patient.query.get(d.patient_id) if d.patient_id else None
        report = Report.query.filter_by(diagnosis_id=d.id).order_by(
            Report.version_no.desc()).first()
        top_probs = DiseaseProbability.query.filter_by(diagnosis_id=d.id)\
            .order_by(DiseaseProbability.probability.desc()).limit(3).all()
        items.append({
            **d.to_dict(),
            'patient_name': patient.name if patient else '未知',
            'patient_no': patient.patient_no if patient else '',
            'report': report.to_dict() if report else None,
            'top_diseases': [p.to_dict() for p in top_probs],
        })

    return jsonify({
        'code': 200,
        'data': {
            'items': items,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
        }
    })


@reports_bp.route('/<int:report_id>', methods=['GET'])
@token_required
@role_required('admin', 'doctor')  # B-10: 报告详情仅医护可见（患者走 /patient/report/<id>）
def get_report(report_id):
    """获取报告详情"""
    report = Report.query.get_or_404(report_id)
    return jsonify({'code': 200, 'data': report.to_dict()})


@reports_bp.route('/<int:report_id>', methods=['PUT'])
@token_required
@role_required('admin', 'doctor')
def update_report(report_id):
    """医生编辑报告"""
    report = Report.query.get_or_404(report_id)
    data = request.get_json()

    if 'doctor_edited_content' in data:
        report.doctor_edited_content = data['doctor_edited_content']
    if 'findings' in data:
        report.findings = data['findings']
    if 'impression' in data:
        report.impression = data['impression']
    if 'recommendations' in data:
        report.recommendations = data['recommendations']
    if 'editor_notes' in data:
        report.editor_notes = data['editor_notes']

    # 创建新版本
    report.version_no = Report.query.filter_by(
        diagnosis_id=report.diagnosis_id).count() + 1
    report.status = 'submitted'
    db.session.commit()

    _log_audit(request.current_user_id, 'EDIT_REPORT', 'report', report_id)
    return jsonify({'code': 200, 'data': report.to_dict()})


@reports_bp.route('/<int:report_id>/approve', methods=['POST'])
@token_required
@role_required('admin', 'doctor')
def approve_report(report_id):
    """审核通过报告"""
    report = Report.query.get_or_404(report_id)
    report.status = 'approved'
    report.signed_by = request.current_user_id
    report.signed_at = datetime.now()
    report.final_content = report.doctor_edited_content or report.ai_generated_content

    # 更新诊断状态
    diagnosis = Diagnosis.query.get(report.diagnosis_id)
    if diagnosis:
        diagnosis.report_status = 'reviewed'
        diagnosis.reviewed_at = datetime.now()
        diagnosis.reviewed_by = request.current_user_id

    db.session.commit()
    _log_audit(request.current_user_id, 'APPROVE_REPORT', 'report', report_id)
    return jsonify({'code': 200, 'message': '报告已审核通过'})


@reports_bp.route('/<int:report_id>/reject', methods=['POST'])
@token_required
@role_required('admin', 'doctor')
def reject_report(report_id):
    """拒绝报告"""
    report = Report.query.get_or_404(report_id)
    data = request.get_json()
    report.status = 'rejected'
    report.reject_reason = data.get('reason', '')

    # 更新诊断状态
    diagnosis = Diagnosis.query.get(report.diagnosis_id)
    if diagnosis:
        diagnosis.report_status = 'rejected'

    db.session.commit()
    _log_audit(request.current_user_id, 'REJECT_REPORT', 'report', report_id)
    return jsonify({'code': 200, 'message': '报告已拒绝'})


@reports_bp.route('/<int:report_id>/regenerate', methods=['POST'])
@token_required
@role_required('admin', 'doctor')
def regenerate_report(report_id):
    """重新生成AI报告"""
    report = Report.query.get_or_404(report_id)
    diagnosis = Diagnosis.query.get(report.diagnosis_id)
    if not diagnosis:
        return jsonify({'code': 404, 'message': '诊断记录不存在'}), 404

    from models.diagnosis import DiseaseProbability
    from models.patient import Patient
    from services.report_service import create_diagnosis_report

    probs = DiseaseProbability.query.filter_by(diagnosis_id=diagnosis.id).all()
    probabilities = [p.to_dict() for p in probs]
    patient = Patient.query.get(
        diagnosis.patient_id) if diagnosis.patient_id else None
    patient_info = patient.to_dict() if patient else None

    report_data = create_diagnosis_report(probabilities, patient_info)

    new_report = Report(
        diagnosis_id=diagnosis.id,
        version_no=report.version_no + 1,
        ai_generated_content=report_data['ai_generated_content'],
        findings=report_data['findings'],
        impression=report_data['impression'],
        recommendations=report_data['recommendations'],
        ai_model_used=report_data['ai_model_used'],
        status='draft',
    )
    db.session.add(new_report)
    db.session.commit()

    return jsonify({'code': 200, 'data': new_report.to_dict()})


def _log_audit(user_id, action, resource_type, resource_id):
    try:
        log = AuditLog(user_id=user_id, action=action,
                       resource_type=resource_type, resource_id=resource_id,
                       ip_address=request.remote_addr)
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()
