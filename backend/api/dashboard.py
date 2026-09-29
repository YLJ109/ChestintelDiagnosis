"""数据看板API"""
from datetime import datetime, timedelta
from flask import Blueprint, jsonify
from extensions import db
from models.diagnosis import Diagnosis, DiseaseProbability
from models.report import Report
from models.user import User
from models.audit import AuditLog
from utils.auth import token_required, role_required

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/v1/dashboard')


@dashboard_bp.route('/stats', methods=['GET'])
@token_required
@role_required('admin', 'doctor', 'nurse')  # B-13: 仪表盘仅医护可见
def get_stats():
    """获取看板统计数据"""
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    month_start = datetime.combine(today.replace(day=1), datetime.min.time())

    # 今日诊断数
    today_count = Diagnosis.query.filter(
        Diagnosis.created_at >= today_start).count()

    # 本月累计诊断数
    month_count = Diagnosis.query.filter(
        Diagnosis.created_at >= month_start).count()

    # 待审核报告数
    pending_count = Diagnosis.query.filter_by(
        report_status='pending_review').count()

    # 高危病例数（任一疾病概率>0.7）
    high_risk_count = db.session.query(db.func.count(db.distinct(DiseaseProbability.diagnosis_id)))\
        .filter(DiseaseProbability.threshold_exceeded == True).scalar() or 0

    # 平均诊断响应时间（简化：从创建到审核的平均小时数）
    reviewed = Diagnosis.query.filter(
        Diagnosis.reviewed_at.isnot(None),
        Diagnosis.created_at >= month_start
    ).all()
    avg_response_hours = 0
    if reviewed:
        total_hours = sum(
            (d.reviewed_at - d.created_at).total_seconds() / 3600
            for d in reviewed
        )
        avg_response_hours = round(total_hours / len(reviewed), 1)

    return jsonify({
        'code': 200,
        'data': {
            'today_count': today_count,
            'month_count': month_count,
            'pending_count': pending_count,
            'high_risk_count': high_risk_count,
            'avg_response_hours': avg_response_hours,
        }
    })


@dashboard_bp.route('/disease-distribution', methods=['GET'])
@token_required
@role_required('admin', 'doctor', 'nurse')  # B-13: 仪表盘仅医护可见
def get_disease_distribution():
    """获取疾病分布数据（近30天）"""
    thirty_days_ago = datetime.now() - timedelta(days=30)

    results = db.session.query(
        DiseaseProbability.disease_code,
        DiseaseProbability.disease_name_zh,
        db.func.count(DiseaseProbability.id).label('count')
    ).join(Diagnosis).filter(
        Diagnosis.created_at >= thirty_days_ago,
        DiseaseProbability.probability >= 0.5
    ).group_by(
        DiseaseProbability.disease_code,
        DiseaseProbability.disease_name_zh
    ).order_by(db.desc('count')).all()

    return jsonify({
        'code': 200,
        'data': [
            {'disease_code': r[0], 'disease_name_zh': r[1], 'count': r[2]}
            for r in results
        ]
    })


@dashboard_bp.route('/trend', methods=['GET'])
@token_required
@role_required('admin', 'doctor', 'nurse')  # B-13: 仪表盘仅医护可见
def get_diagnosis_trend():
    """获取诊断趋势数据（近30天每日诊断量）"""
    thirty_days_ago = datetime.now() - timedelta(days=30)

    results = db.session.query(
        db.func.date(Diagnosis.created_at).label('date'),
        db.func.count(Diagnosis.id).label('count')
    ).filter(
        Diagnosis.created_at >= thirty_days_ago
    ).group_by(
        db.func.date(Diagnosis.created_at)
    ).order_by('date').all()

    return jsonify({
        'code': 200,
        'data': [
            {'date': str(r[0]), 'count': r[1]}
            for r in results
        ]
    })


@dashboard_bp.route('/system-overview', methods=['GET'])
@token_required
@role_required('admin')
def get_system_overview():
    """管理员系统概览"""
    # 系统资源（psutil可能未安装）
    system_info = {
        'cpu_percent': None,
        'memory_percent': None,
        'memory_total_gb': None,
        'memory_used_gb': None,
        'disk_percent': None,
        'disk_total_gb': None,
        'disk_used_gb': None,
    }
    try:
        import psutil
        import os
        system_info['cpu_percent'] = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        system_info['memory_percent'] = memory.percent
        system_info['memory_total_gb'] = round(memory.total / (1024**3), 1)
        system_info['memory_used_gb'] = round(memory.used / (1024**3), 1)
        disk = psutil.disk_usage(os.path.dirname(os.path.abspath(__file__)))
        system_info['disk_percent'] = disk.percent
        system_info['disk_total_gb'] = round(disk.total / (1024**3), 1)
        system_info['disk_used_gb'] = round(disk.used / (1024**3), 1)
    except ImportError:
        pass
    except Exception:
        pass

    # 用户统计
    total_users = User.query.count()
    active_users = User.query.filter_by(status='active').count()

    # 诊断统计
    total_diagnoses = Diagnosis.query.count()
    today_diagnoses = Diagnosis.query.filter(
        Diagnosis.created_at >= datetime.combine(
            datetime.now().date(), datetime.min.time())
    ).count()

    # 模型信息
    model_loaded = False
    try:
        from services.ai_service import is_model_loaded
        model_loaded = is_model_loaded()
    except Exception:
        pass

    return jsonify({
        'code': 200,
        'data': {
            'system': system_info,
            'users': {
                'total': total_users,
                'active': active_users,
            },
            'diagnoses': {
                'total': total_diagnoses,
                'today': today_diagnoses,
            },
            'model': {
                'loaded': model_loaded,
            },
        }
    })
