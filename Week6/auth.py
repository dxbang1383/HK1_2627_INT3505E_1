
import hashlib
import secrets
import time
from collections import defaultdict
from functools import wraps

import bcrypt
from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError
from flask import g, jsonify, request
from flask_jwt_extended import JWTManager, get_jwt, get_jwt_identity

from models import Post, RevokedToken, User, db

jwt = JWTManager()

ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, type=Type.ID)

_DUMMY_BCRYPT_HASH = bcrypt.hashpw(b"dummy-password-for-timing-safety", bcrypt.gensalt(rounds=10))


def hash_password_bcrypt(plain_password: str) -> str:
    pwd_bytes = plain_password.encode("utf-8")[:72]
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt(rounds=10)).decode("utf-8")


def hash_password_argon2(plain_password: str) -> str:
    return ph.hash(plain_password)


def verify_password(plain_password: str, stored_hash: str | None) -> bool:

    if not stored_hash:
        bcrypt.checkpw(plain_password.encode("utf-8")[:72], _DUMMY_BCRYPT_HASH)
        return False

    if stored_hash.startswith("$argon2"):
        try:
            return ph.verify(stored_hash, plain_password)
        except VerifyMismatchError:
            return False

    pwd_bytes = plain_password.encode("utf-8")[:72]
    stored_bytes = stored_hash.encode("utf-8") if isinstance(stored_hash, str) else stored_hash
    return bcrypt.checkpw(pwd_bytes, stored_bytes)


def mint_key(prefix: str = "sk_live") -> tuple[str, str]:

    raw = secrets.token_urlsafe(32)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8]
    plain = f"{prefix}_{raw}_{digest}"
    store = hashlib.sha256(plain.encode("utf-8")).hexdigest()
    return plain, store


def load_permissions(user_id: int | str) -> dict:

    user = db.session.get(User, int(user_id))
    if not user or not user.is_active:
        return {"roles": [], "scopes": []}
    return {
        "roles": user.get_roles(),
        "scopes": user.get_scopes(),
    }


def revoke_token_jti(jti: str, token_type: str, user_id: int | str) -> None:

    existing = db.session.scalar(db.select(RevokedToken).filter_by(jti=jti))
    if not existing:
        db.session.add(
            RevokedToken(jti=jti, token_type=token_type, user_id=int(user_id))
        )
        db.session.commit()


# =====================================================================
# JWT Callbacks & Error Handlers (Slide 15, 18)
# =====================================================================

@jwt.token_in_blocklist_loader
def check_if_token_revoked(_jwt_header, jwt_payload: dict) -> bool:
    jti = jwt_payload.get("jti")
    if not jti:
        return True
    revoked = db.session.scalar(db.select(RevokedToken.id).filter_by(jti=jti))
    return revoked is not None


@jwt.unauthorized_loader
def handle_missing_token(reason: str):
    return jsonify({"error": "unauthorized", "message": reason}), 401


@jwt.invalid_token_loader
def handle_invalid_token(reason: str):
    # Xử lý riêng lỗi dùng nhầm Access Token cho Refresh Endpoint (hoặc ngược lại)
    if "Only refresh tokens are allowed" in reason or "Only non-refresh tokens are allowed" in reason:
        return jsonify({"error": "invalid_token_type", "message": reason}), 401
    return jsonify({"error": "unauthorized", "message": reason}), 401


@jwt.expired_token_loader
def handle_expired_token(_jwt_header, _jwt_payload):
    return jsonify({"error": "token_expired", "message": "Token has expired"}), 401


@jwt.revoked_token_loader
def handle_revoked_token(_jwt_header, _jwt_payload):
    return jsonify({"error": "token_revoked", "message": "Token has been revoked"}), 401


# =====================================================================
# 3 LỚP DECORATOR PHÂN QUYỀN (Slide 24, 25, 26)
# =====================================================================

def load_current_user():
    """Nạp thông tin user hiện tại vào flask.g từ JWT identity và claims."""
    uid = get_jwt_identity()
    claims = get_jwt()
    user = db.session.get(User, int(uid))
    if not user or not user.is_active:
        return None
    g.current_user = {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "roles": claims.get("roles", user.get_roles()),
        "scopes": claims.get("scopes", user.get_scopes()),
    }
    return g.current_user


def require_roles(*allowed_roles: str):

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            current = getattr(g, "current_user", None) or load_current_user()
            if not current:
                return jsonify({"error": "unauthorized", "message": "User account is inactive or missing"}), 401
            user_roles = set(current.get("roles", []))
            if not (user_roles & set(allowed_roles)):
                return jsonify({
                    "error": "forbidden",
                    "message": "Insufficient role permissions",
                    "need_one_of": list(allowed_roles),
                }), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_scopes(*needed_scopes: str):

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            current = getattr(g, "current_user", None) or load_current_user()
            if not current:
                return jsonify({"error": "unauthorized", "message": "User account is inactive or missing"}), 401
            granted_scopes = set(get_jwt().get("scopes", []))
            if not set(needed_scopes).issubset(granted_scopes):
                return jsonify({
                    "error": "insufficient_scope",
                    "message": f"Missing required scope: {', '.join(needed_scopes)}",
                    "need_all_of": list(needed_scopes),
                }), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def user_owns_resource(param: str = "id", allow_public_read: bool = False):

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            current = getattr(g, "current_user", None) or load_current_user()
            if not current:
                return jsonify({"error": "unauthorized", "message": "User account is inactive or missing"}), 401

            resource_id = kwargs.get(param)
            if resource_id is None or resource_id < 1:
                return jsonify({"error": "bad_request", "message": "Post id must be a positive integer"}), 400

            post = db.session.get(Post, resource_id)
            if not post:
                return jsonify({"error": "not_found", "message": "Post not found"}), 404

            is_owner = str(post.owner_id) == str(current["id"])
            is_admin = "admin" in current.get("roles", [])

            if allow_public_read and post.visibility == "public":
                g.target_post = post
                return fn(*args, **kwargs)

            if not is_owner and not is_admin:
                return jsonify({
                    "error": "forbidden",
                    "message": "You do not have permission to access this resource",
                }), 403

            g.target_post = post
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# =====================================================================
# Rate Limiter đơn giản theo cửa sổ thời gian (Chống OWASP API2:2023)
# =====================================================================

class InMemoryRateLimiter:
    def __init__(self):
        self._hits: dict[str, list[float]] = defaultdict(list)

    def reset(self):
        self._hits.clear()

    def check(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
        now = time.monotonic()
        cutoff = now - window_seconds
        history = [t for t in self._hits[key] if t > cutoff]
        if len(history) >= max_requests:
            self._hits[key] = history
            return False, 0
        history.append(now)
        self._hits[key] = history
        return True, max_requests - len(history)


rate_limiter = InMemoryRateLimiter()


def rate_limit(bucket: str, max_requests: int = 5, window_seconds: int = 60):
    """Decorator giới hạn tần suất gọi API trên mỗi IP."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            client_ip = request.remote_addr or "127.0.0.1"
            key = f"{bucket}:{client_ip}"
            allowed, remaining = rate_limiter.check(key, max_requests, window_seconds)
            if not allowed:
                resp = jsonify({
                    "error": "rate_limit_exceeded",
                    "message": f"Too many requests. Please try again in {window_seconds} seconds.",
                })
                resp.status_code = 429
                resp.headers["Retry-After"] = str(window_seconds)
                return resp

            response = fn(*args, **kwargs)
            if isinstance(response, tuple):
                resp_obj, status = response[0], response[1]
                resp_obj.headers["X-RateLimit-Limit"] = str(max_requests)
                resp_obj.headers["X-RateLimit-Remaining"] = str(remaining)
                return resp_obj, status
            response.headers["X-RateLimit-Limit"] = str(max_requests)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            return response
        return wrapper
    return decorator
