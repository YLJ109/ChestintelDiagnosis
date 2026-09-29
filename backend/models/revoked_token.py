"""已吊销 Token 黑名单（B-22：登出后 Token 立即失效）"""
from datetime import datetime
from extensions import db


class RevokedToken(db.Model):
    __tablename__ = 'revoked_tokens'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    jti = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, index=True)
    revoked_at = db.Column(db.DateTime, default=datetime.now)
    # Token 原过期时间（UTC naive），过期后黑名单记录可清理
    expires_at = db.Column(db.DateTime)
