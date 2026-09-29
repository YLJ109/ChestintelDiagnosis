"""模型权重管理API"""
import os
import re
import hashlib
import json
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from extensions import db
from models.model_weight import ModelWeight
from models.audit import AuditLog
from utils.auth import token_required, role_required
from services.ai_service import load_model, get_runtime_params, update_runtime_params

model_weights_bp = Blueprint('model_weights', __name__, url_prefix='/api/v1/model-weights')


@model_weights_bp.route('/', methods=['GET'])
@token_required
@role_required('admin')
def get_weights():
    """获取权重文件列表"""
    weights = ModelWeight.query.order_by(ModelWeight.uploaded_at.desc()).all()
    return jsonify({
        'code': 200,
        'data': [w.to_dict() for w in weights]
    })


@model_weights_bp.route('/', methods=['POST'])
@token_required
@role_required('admin')
def upload_weight():
    """上传新权重文件"""
    file = request.files.get('file')
    if not file:
        return jsonify({'code': 400, 'message': '请上传权重文件'}), 400

    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in ('pth', 'pt', 'onnx'):
        return jsonify({'code': 400, 'message': '仅支持 .pth/.pt/.onnx 格式'}), 400

    version_name = request.form.get('version_name', '').strip()
    if not version_name:
        return jsonify({'code': 400, 'message': '版本号不能为空'}), 400
    # 白名单校验：仅允许字母数字与 . - _，杜绝路径穿越（如 ../../x）
    if not re.match(r'^[\w.\-]+$', version_name):
        return jsonify({'code': 400, 'message': '版本号包含非法字符'}), 400

    if ModelWeight.query.filter_by(version_name=version_name).first():
        return jsonify({'code': 400, 'message': '版本号已存在'}), 400

    # 保存文件
    model_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'model_files')
    os.makedirs(model_dir, exist_ok=True)
    filename = f"{secure_filename(version_name)}_{secure_filename(file.filename)}"
    filepath = os.path.join(model_dir, filename)
    file.save(filepath)

    # 计算文件大小和哈希
    file_size = os.path.getsize(filepath)
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for block in iter(lambda: f.read(8192), b''):
            sha256.update(block)
    file_hash = sha256.hexdigest()

    weight = ModelWeight(
        version_name=version_name,
        file_path=filepath,
        file_size=file_size,
        file_hash=file_hash,
        architecture=request.form.get('architecture', 'DenseNet-121'),
        training_dataset=request.form.get('training_dataset', 'NIH ChestX-ray14'),
        metrics=request.form.get('metrics'),
        is_active=False,
        uploaded_by=request.current_user_id,
        description=request.form.get('description'),
    )
    db.session.add(weight)
    db.session.commit()

    _log_audit(request.current_user_id, 'UPLOAD_MODEL', 'model_weight', weight.id)
    return jsonify({'code': 200, 'data': weight.to_dict()})


@model_weights_bp.route('/<int:weight_id>/activate', methods=['POST'])
@token_required
@role_required('admin')
def activate_weight(weight_id):
    """激活模型权重版本"""
    weight = ModelWeight.query.get_or_404(weight_id)

    # 停用其他版本
    ModelWeight.query.update({'is_active': False})

    # 激活当前版本
    weight.is_active = True
    db.session.commit()

    # 热加载模型
    if os.path.isfile(weight.file_path):
        load_model(weight.file_path, version_name=weight.version_name)

    _log_audit(request.current_user_id, 'ACTIVATE_MODEL', 'model_weight', weight_id)
    return jsonify({'code': 200, 'message': f'模型版本 {weight.version_name} 已激活'})


@model_weights_bp.route('/<int:weight_id>', methods=['DELETE'])
@token_required
@role_required('admin')
def delete_weight(weight_id):
    """删除权重文件"""
    weight = ModelWeight.query.get_or_404(weight_id)
    if weight.is_active:
        return jsonify({'code': 400, 'message': '不能删除当前激活的模型版本'}), 400

    # 删除文件
    if os.path.isfile(weight.file_path):
        os.remove(weight.file_path)

    db.session.delete(weight)
    db.session.commit()
    _log_audit(request.current_user_id, 'DELETE_MODEL', 'model_weight', weight_id)
    return jsonify({'code': 200, 'message': '权重文件已删除'})


def _log_audit(user_id, action, resource_type, resource_id):
    try:
        log = AuditLog(user_id=user_id, action=action,
                       resource_type=resource_type, resource_id=resource_id,
                       ip_address=request.remote_addr)
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()


@model_weights_bp.route('/active-info', methods=['GET'])
@token_required
@role_required('admin')
def get_active_info():
    """获取当前激活模型信息及运行时参数"""
    runtime = get_runtime_params()

    # 获取激活的权重文件详情
    active_weight = ModelWeight.query.filter_by(is_active=True).first()
    weight_info = active_weight.to_dict() if active_weight else None

    return jsonify({
        'code': 200,
        'data': {
            'runtime': runtime,
            'active_weight': weight_info,
        }
    })


@model_weights_bp.route('/params', methods=['PUT'])
@token_required
@role_required('admin')
def update_params():
    """更新运行时参数"""
    data = request.get_json()
    updated = update_runtime_params(data)

    if not updated:
        return jsonify({'code': 400, 'message': '没有可更新的参数'}), 400

    _log_audit(request.current_user_id, 'UPDATE_MODEL_PARAMS', 'model_params', 0)
    return jsonify({
        'code': 200,
        'data': get_runtime_params(),
        'message': f'参数已更新: {list(updated.keys())}'
    })
