"""诊断审批API"""
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from extensions import db
from models.approval import Approval
from models.diagnosis import Diagnosis, DiseaseProbability
from models.report import Report
from models.audit import AuditLog
from utils.auth import token_required, role_required

approvals_bp = Blueprint('approvals', __name__, url_prefix='/api/v1/approvals')


@approvals_bp.route('/', methods=['GET'])
@token_required
@role_required('admin', 'doctor')  # ⚠️ P1-1: 添加权限控制
def get_approvals():
    """获取审批列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    priority = request.args.get('priority')
    keyword = request.args.get('keyword', '').strip()

    query = Approval.query

    if status:
        # F-10: 支持"rejected,revision_needed"逗号分隔多状态查询
        if ',' in status:
            query = query.filter(Approval.status.in_(
                [s.strip() for s in status.split(',') if s.strip()]))
        else:
            query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)

    # 关键词搜索（患者姓名/编号）
    if keyword:
        from models.patient import Patient
        patient_ids = [p.id for p in Patient.query.filter(
            db.or_(Patient.name.like(f'%{keyword}%'),
                   Patient.patient_no.like(f'%{keyword}%'))
        ).all()]
        if patient_ids:
            query = query.filter(Approval.patient_id.in_(patient_ids))
        else:
            query = query.filter(Approval.patient_id == -1)  # 无匹配

    query = query.order_by(Approval.submitted_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # 批量加载关联数据，避免N+1查询
    from models.patient import Patient
    from models.user import User
    items = pagination.items
    patient_ids = list(set(a.patient_id for a in items if a.patient_id))
    submitter_ids = list(set(a.submitter_id for a in items if a.submitter_id))
    diagnosis_ids = list(set(a.diagnosis_id for a in items))

    patients_map = {p.id: p for p in Patient.query.filter(
        Patient.id.in_(patient_ids)).all()} if patient_ids else {}
    users_map = {u.id: u for u in User.query.filter(
        User.id.in_(submitter_ids)).all()} if submitter_ids else {}
    diagnoses_map = {d.id: d for d in Diagnosis.query.filter(
        Diagnosis.id.in_(diagnosis_ids)).all()} if diagnosis_ids else {}

    result_items = []
    for a in items:
        item = a.to_dict()
        patient = patients_map.get(a.patient_id)
        item['patient_name'] = patient.name if patient else '-'
        item['patient_no'] = patient.patient_no if patient else '-'
        item['patient_gender'] = patient.gender if patient else '-'
        item['patient_age'] = patient.age if patient else None

        submitter = users_map.get(a.submitter_id)
        item['submitter_name'] = submitter.real_name if submitter else '-'

        diagnosis = diagnoses_map.get(a.diagnosis_id)
        item['diagnosis_no'] = diagnosis.diagnosis_no if diagnosis else f'DX-{a.diagnosis_id}'
        item['diagnosis_type'] = diagnosis.diagnosis_type if diagnosis else '-'
        item['image_url'] = f"/static/{diagnosis.image_path}" if diagnosis and diagnosis.image_path else None
        item['heatmap_url'] = f"/static/{diagnosis.heatmap_path}" if diagnosis and diagnosis.heatmap_path else None

        # Top disease
        if diagnosis:
            top_prob = DiseaseProbability.query.filter_by(diagnosis_id=diagnosis.id)\
                .order_by(DiseaseProbability.probability.desc()).first()
            if top_prob:
                item['top_disease'] = top_prob.disease_name_zh
                item['top_probability'] = round(top_prob.probability, 4)
                item['top_threshold_exceeded'] = top_prob.threshold_exceeded

        result_items.append(item)

    return jsonify({
        'code': 200,
        'data': {
            'items': result_items,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
        }
    })


@approvals_bp.route('/<int:approval_id>', methods=['GET'])
@token_required
@role_required('admin', 'doctor')  # B-09: 审批详情仅医护可见
def get_approval(approval_id):
    """获取审批详情"""
    approval = Approval.query.get_or_404(approval_id)
    return jsonify({'code': 200, 'data': approval.to_dict(include_detail=True)})


@approvals_bp.route('/', methods=['POST'])
@token_required
@role_required('admin', 'doctor')  # B-09: 提交审批仅医护可用
def create_approval():
    """提交审批申请"""
    data = request.get_json()
    diagnosis_id = data.get('diagnosis_id')

    if not diagnosis_id:
        return jsonify({'code': 400, 'message': '诊断记录ID不能为空'}), 400

    diagnosis = Diagnosis.query.get(diagnosis_id)
    if not diagnosis:
        return jsonify({'code': 404, 'message': '诊断记录不存在'}), 404

    # 检查是否已有审批记录
    existing = Approval.query.filter_by(diagnosis_id=diagnosis_id).first()
    if existing:
        return jsonify({'code': 400, 'message': '该诊断已有审批记录'}), 400

    # 查找关联的报告
    report = Report.query.filter_by(diagnosis_id=diagnosis_id).order_by(
        Report.version_no.desc()).first()

    approval = Approval(
        diagnosis_id=diagnosis_id,
        report_id=report.id if report else None,
        patient_id=diagnosis.patient_id,
        submitter_id=request.current_user_id,
        priority=data.get('priority', 'normal'),
        review_notes=data.get('review_notes'),
    )
    db.session.add(approval)

    # 更新诊断状态
    diagnosis.report_status = 'pending_review'

    db.session.commit()
    _log_audit(request.current_user_id,
               'CREATE_APPROVAL', 'approval', approval.id)
    return jsonify({'code': 200, 'data': approval.to_dict()})


@approvals_bp.route('/<int:approval_id>', methods=['PUT'])
@token_required
@role_required('admin', 'doctor')  # B-09: 修改审批仅医护可用
def update_approval(approval_id):
    """更新审批记录（仅pending状态可修改）"""
    approval = Approval.query.get_or_404(approval_id)

    if approval.status != 'pending':
        return jsonify({'code': 400, 'message': '仅待审批状态可修改'}), 400

    data = request.get_json()
    if 'priority' in data:
        approval.priority = data['priority']
    if 'review_notes' in data:
        approval.review_notes = data['review_notes']

    db.session.commit()
    return jsonify({'code': 200, 'data': approval.to_dict()})


@approvals_bp.route('/<int:approval_id>', methods=['DELETE'])
@token_required
@role_required('admin')
def delete_approval(approval_id):
    """删除审批记录（仅admin）"""
    approval = Approval.query.get_or_404(approval_id)
    if approval.status == 'pending':
        return jsonify({'code': 400, 'message': '不能删除待审批记录'}), 400

    db.session.delete(approval)
    db.session.commit()
    _log_audit(request.current_user_id,
               'DELETE_APPROVAL', 'approval', approval_id)
    return jsonify({'code': 200, 'message': '审批记录已删除'})


@approvals_bp.route('/<int:approval_id>/approve', methods=['POST'])
@token_required
@role_required('admin', 'doctor')  # ⚠️ P1-1: 添加权限控制
def approve_approval(approval_id):
    """审批通过"""
    approval = Approval.query.get_or_404(approval_id)

    if approval.status != 'pending':
        return jsonify({'code': 400, 'message': '仅待审批状态可审批'}), 400

    data = request.get_json() or {}

    approval.status = 'approved'
    approval.reviewer_id = request.current_user_id
    approval.reviewed_at = datetime.now()
    if data.get('review_notes'):
        approval.review_notes = data['review_notes']

    # 更新关联的诊断和报告状态
    diagnosis = Diagnosis.query.get(approval.diagnosis_id)
    if diagnosis:
        diagnosis.report_status = 'reviewed'
        diagnosis.reviewed_by = request.current_user_id
        diagnosis.reviewed_at = datetime.now()

    if approval.report_id:
        report = Report.query.get(approval.report_id)
        if report:
            report.status = 'approved'

    db.session.commit()
    _log_audit(request.current_user_id,
               'APPROVE_DIAGNOSIS', 'approval', approval_id)
    return jsonify({'code': 200, 'data': approval.to_dict(include_detail=True)})


@approvals_bp.route('/<int:approval_id>/reject', methods=['POST'])
@token_required
@role_required('admin', 'doctor')  # ⚠️ P1-1: 添加权限控制
def reject_approval(approval_id):
    """审批驳回"""
    approval = Approval.query.get_or_404(approval_id)

    if approval.status != 'pending':
        return jsonify({'code': 400, 'message': '仅待审批状态可驳回'}), 400

    data = request.get_json() or {}
    reject_reason = data.get('reject_reason', '').strip()

    if not reject_reason:
        return jsonify({'code': 400, 'message': '驳回原因不能为空'}), 400

    approval.status = 'rejected'
    approval.reviewer_id = request.current_user_id
    approval.reviewed_at = datetime.now()
    approval.reject_reason = reject_reason
    if data.get('review_notes'):
        approval.review_notes = data['review_notes']

    # 更新关联的诊断状态
    diagnosis = Diagnosis.query.get(approval.diagnosis_id)
    if diagnosis:
        diagnosis.report_status = 'rejected'
        diagnosis.reviewed_by = request.current_user_id
        diagnosis.reviewed_at = datetime.now()

    if approval.report_id:
        report = Report.query.get(approval.report_id)
        if report:
            report.status = 'rejected'
            report.reject_reason = reject_reason

    db.session.commit()
    _log_audit(request.current_user_id,
               'REJECT_DIAGNOSIS', 'approval', approval_id)
    return jsonify({'code': 200, 'data': approval.to_dict(include_detail=True)})


@approvals_bp.route('/<int:approval_id>/revise', methods=['POST'])
@token_required
@role_required('admin', 'doctor')  # ⚠️ P1-1: 添加权限控制
def request_revision(approval_id):
    """请求修改"""
    approval = Approval.query.get_or_404(approval_id)

    if approval.status != 'pending':
        return jsonify({'code': 400, 'message': '仅待审批状态可请求修改'}), 400

    data = request.get_json() or {}
    review_notes = data.get('review_notes', '').strip()

    if not review_notes:
        return jsonify({'code': 400, 'message': '修改意见不能为空'}), 400

    approval.status = 'revision_needed'
    approval.reviewer_id = request.current_user_id
    approval.reviewed_at = datetime.now()
    approval.review_notes = review_notes

    # 更新关联的诊断状态
    diagnosis = Diagnosis.query.get(approval.diagnosis_id)
    if diagnosis:
        diagnosis.report_status = 'revision_needed'

    if approval.report_id:
        report = Report.query.get(approval.report_id)
        if report:
            report.status = 'revision_needed'

    db.session.commit()
    _log_audit(request.current_user_id,
               'REQUEST_REVISION', 'approval', approval_id)
    return jsonify({'code': 200, 'data': approval.to_dict(include_detail=True)})


@approvals_bp.route('/stats', methods=['GET'])
@token_required
@role_required('admin', 'doctor')  # B-09: 审批统计仅医护可见
def get_approval_stats():
    """获取审批统计"""
    total = Approval.query.count()
    pending = Approval.query.filter_by(status='pending').count()
    approved = Approval.query.filter_by(status='approved').count()
    rejected = Approval.query.filter_by(status='rejected').count()
    revision = Approval.query.filter_by(status='revision_needed').count()

    # 统计待审批但无审批记录的诊断数
    approved_diagnosis_ids = db.session.query(
        Approval.diagnosis_id).distinct().all()
    id_list = [r[0] for r in approved_diagnosis_ids]
    unsubmitted_query = Diagnosis.query.filter(
        Diagnosis.report_status == 'pending_review')
    if id_list:
        unsubmitted_query = unsubmitted_query.filter(
            ~Diagnosis.id.in_(id_list))
    unsubmitted = unsubmitted_query.count()

    return jsonify({
        'code': 200,
        'data': {
            'total': total,
            'pending': pending,
            'approved': approved,
            'rejected': rejected,
            'revision_needed': revision,
            'unsubmitted': unsubmitted,
        }
    })


@approvals_bp.route('/sync-missing', methods=['POST'])
@token_required
@role_required('admin')
def sync_missing_approvals():
    """为所有pending_review但无审批记录的诊断补建审批记录"""
    approved_diagnosis_ids = db.session.query(
        Approval.diagnosis_id).distinct().all()
    id_list = [r[0] for r in approved_diagnosis_ids]
    query = Diagnosis.query.filter(Diagnosis.report_status == 'pending_review')
    if id_list:
        query = query.filter(~Diagnosis.id.in_(id_list))

    missing = query.all()
    created = 0
    for d in missing:
        report = Report.query.filter_by(diagnosis_id=d.id).order_by(
            Report.version_no.desc()).first()
        approval = Approval(
            diagnosis_id=d.id,
            report_id=report.id if report else None,
            patient_id=d.patient_id,
            submitter_id=d.doctor_id or d.technician_id or request.current_user_id,
            status='pending',
            priority='normal',
        )
        db.session.add(approval)
        created += 1

    db.session.commit()
    _log_audit(request.current_user_id,
               'SYNC_MISSING_APPROVALS', 'approval', None)
    return jsonify({'code': 200, 'data': {'created': created}})


def _log_audit(user_id, action, resource_type, resource_id):
    try:
        log = AuditLog(user_id=user_id, action=action,
                       resource_type=resource_type, resource_id=resource_id,
                       ip_address=request.remote_addr)
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()
