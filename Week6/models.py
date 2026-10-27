from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utc_now():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    pwd_hash = db.Column(db.String(255), nullable=False)
    roles = db.Column(db.String(120), nullable=False, default="user")
    scopes = db.Column(db.String(255), nullable=False, default="posts:read,posts:write")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    def get_roles(self) -> list[str]:
        return [r.strip() for r in self.roles.split(",") if r.strip()]

    def get_scopes(self) -> list[str]:
        return [s.strip() for s in self.scopes.split(",") if s.strip()]

    def to_author_dto(self) -> dict:
        """
        DTO an toàn (OWASP API3:2023 - BOPLA):
        Chỉ trả về id và username, tuyệt đối không trả pwd_hash hay email riêng tư.
        """
        return {
            "id": self.id,
            "username": self.username,
        }


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    visibility = db.Column(db.String(20), nullable=False, default="public")  # public | friends | private
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    owner = db.relationship("User", backref=db.backref("posts", lazy=True))

    def to_dto(self) -> dict:
        created_iso = (
            self.created_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if self.created_at
            else None
        )
        return {
            "id": self.id,
            "content": self.content,
            "visibility": self.visibility,
            "author": self.owner.to_author_dto() if self.owner else {"id": self.owner_id, "username": "unknown"},
            "created_at": created_iso,
        }


class RevokedToken(db.Model):
    """Lưu trữ jti của các JWT đã bị thu hồi (thay thế hoặc bổ trợ cho Redis blocklist)."""

    __tablename__ = "revoked_tokens"

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(64), unique=True, nullable=False, index=True)
    token_type = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
