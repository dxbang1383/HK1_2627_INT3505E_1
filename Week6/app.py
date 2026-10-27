import os
import re
import secrets
from flask import Flask, g, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

from auth import (
    hash_password_argon2,
    hash_password_bcrypt,
    jwt,
    load_permissions,
    rate_limit,
    require_roles,
    require_scopes,
    revoke_token_jti,
    user_owns_resource,
    verify_password,
)
from models import Post, User, db

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ACCESS_EXPIRES_SECONDS = 900       # 15 phút (Slide 15)
REFRESH_EXPIRES_SECONDS = 2592000  # 30 ngày (Slide 15)


def seed_demo_data():
    """Khởi tạo dữ liệu mẫu cho bài tập Social Network API."""
    if db.session.scalar(db.select(User.id).limit(1)) is not None:
        return

    user_an = User(
        id=42,
        email="an@vnu.edu.vn",
        username="nguyen_van_an",
        pwd_hash=hash_password_bcrypt("correct horse battery staple"),
        roles="user",
        scopes="posts:read,posts:write",
    )
    user_binh = User(
        id=78,
        email="binh@vnu.edu.vn",
        username="tran_thi_binh",
        pwd_hash=hash_password_argon2("binh_secret_password"),
        roles="user",
        scopes="posts:read",
    )
    user_limited = User(
        id=99,
        email="guest@vnu.edu.vn",
        username="guest_no_post_scope",
        pwd_hash=hash_password_bcrypt("guest_password_123"),
        roles="viewer",
        scopes="profile:read",  # Không có scope posts:read
    )
    user_admin = User(
        id=1,
        email="admin@vnu.edu.vn",
        username="system_admin",
        pwd_hash=hash_password_argon2("admin_strong_password"),
        roles="admin,manager",
        scopes="posts:read,posts:write,users:read",
    )

    db.session.add_all([user_an, user_binh, user_limited, user_admin])
    db.session.flush()

    post_public = Post(
        id=100,
        content="Chào mừng đến với mạng xã hội SOA Buổi 06! (Bài viết công khai của An)",
        visibility="public",
        owner_id=user_an.id,
    )
    post_private_an = Post(
        id=101,
        content="Nhật ký bí mật của An — chỉ mình An hoặc Admin mới đọc được (Test chống BOLA).",
        visibility="private",
        owner_id=user_an.id,
    )
    post_private_binh = Post(
        id=102,
        content="Bản nháp riêng tư của Bình — An không được phép đọc bài viết này!",
        visibility="private",
        owner_id=user_binh.id,
    )

    db.session.add_all([post_public, post_private_an, post_private_binh])
    db.session.commit()


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)

    # Sinh khoá >= 256-bit nếu chưa đặt biến môi trường (Slide 15, 18)
    default_secret = secrets.token_urlsafe(32)
    default_jwt_secret = secrets.token_urlsafe(32)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", default_secret),
        JWT_SECRET_KEY=os.environ.get("JWT_SECRET_KEY", default_jwt_secret),
        JWT_ACCESS_TOKEN_EXPIRES=ACCESS_EXPIRES_SECONDS,
        JWT_REFRESH_TOKEN_EXPIRES=REFRESH_EXPIRES_SECONDS,
        JWT_ALGORITHM="HS256",
        JWT_DECODE_ALGORITHMS=["HS256"],  # Allowlist thuật toán, chặn alg=none (Slide 18)
        SQLALCHEMY_DATABASE_URI="sqlite:///social_auth_b6.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    jwt.init_app(app)

    with app.app_context():
        db.create_all()
        seed_demo_data()

    # =================================================================
    # ENDPOINT 1: POST /api/auth/login (và alias /auth/login)
    # =================================================================
    @app.post("/api/auth/login")
    @app.post("/auth/login")
    @rate_limit(bucket="auth_login", max_requests=5, window_seconds=60)
    def login():
        if not request.is_json:
            return jsonify({
                "error": "bad_request",
                "message": "Request body must be valid JSON",
            }), 400

        data = request.get_json(silent=True) or {}
        email = data.get("email")
        password = data.get("password")

        if email is None or password is None:
            return jsonify({
                "error": "bad_request",
                "message": "Request body must contain email and password",
            }), 400

        if not isinstance(email, str) or not EMAIL_REGEX.match(email.strip()):
            return jsonify({
                "error": "validation_error",
                "message": "Email format is invalid",
            }), 422

        if not isinstance(password, str) or len(password) < 1:
            return jsonify({
                "error": "validation_error",
                "message": "Password must not be empty",
            }), 422

        user = db.session.scalar(db.select(User).filter_by(email=email.strip().lower()))
        stored_hash = user.pwd_hash if user else None

        # Luôn gọi verify_password kể cả khi user=None để chống Timing Attack
        if not user or not user.is_active or not verify_password(password, stored_hash):
            return jsonify({
                "error": "invalid_credentials",
                "message": "Invalid email or password",
            }), 401

        claims = load_permissions(user.id)
        uid = str(user.id)

        access_token = create_access_token(identity=uid, additional_claims=claims)
        refresh_token = create_refresh_token(identity=uid, additional_claims=claims)

        return jsonify({
            "access": access_token,
            "refresh": refresh_token,
            "token_type": "Bearer",
            "expires_in": ACCESS_EXPIRES_SECONDS,
        }), 200

    # =================================================================
    # ENDPOINT 2: POST /api/auth/refresh (và alias /auth/refresh)
    # =================================================================
    @app.post("/api/auth/refresh")
    @app.post("/auth/refresh")
    @rate_limit(bucket="auth_refresh", max_requests=10, window_seconds=60)
    @jwt_required(refresh=True)
    def refresh():
        uid = get_jwt_identity()
        current_jwt = get_jwt()

        # Kiểm tra tài khoản còn hoạt động và nạp lại quyền mới nhất từ DB (Slide 17)
        user = db.session.get(User, int(uid))
        if not user or not user.is_active:
            return jsonify({
                "error": "unauthorized",
                "message": "User account is inactive or no longer exists",
            }), 401

        # Refresh Token Rotation: thu hồi ngay jti của refresh token vừa sử dụng
        revoke_token_jti(jti=current_jwt["jti"], token_type="refresh", user_id=uid)

        claims = load_permissions(uid)
        new_access = create_access_token(identity=uid, additional_claims=claims)
        new_refresh = create_refresh_token(identity=uid, additional_claims=claims)

        return jsonify({
            "access": new_access,
            "refresh": new_refresh,
            "token_type": "Bearer",
            "expires_in": ACCESS_EXPIRES_SECONDS,
        }), 200

    # =================================================================
    # ENDPOINT BỔ SUNG: POST /api/auth/logout (Thu hồi token theo jti)
    # =================================================================
    @app.post("/api/auth/logout")
    @app.post("/auth/logout")
    @jwt_required(verify_type=False)
    def logout():
        jwt_data = get_jwt()
        uid = get_jwt_identity()
        revoke_token_jti(
            jti=jwt_data["jti"],
            token_type=jwt_data.get("type", "access"),
            user_id=uid,
        )
        return jsonify({"message": "Token revoked successfully"}), 200

    # =================================================================
    # ENDPOINT 3: GET /api/posts/<id> (và alias /posts/<id>)
    # Áp dụng 3 lớp kiểm tra: AuthN -> Scope (posts:read) -> Ownership/BOLA
    # =================================================================
    @app.get("/api/posts/<int:id>")
    @app.get("/posts/<int:id>")
    @jwt_required()
    @require_scopes("posts:read")
    @user_owns_resource(param="id", allow_public_read=True)
    def get_post(id: int):
        post: Post = g.target_post
        return jsonify(post.to_dto()), 200

    # =================================================================
    # ENDPOINT MINH HỌA SLIDE 25: DELETE /api/posts/<id>
    # Chồng đủ 4 decorator: AuthN + Role + Scope + Ownership
    # =================================================================
    @app.delete("/api/posts/<int:id>")
    @app.delete("/posts/<int:id>")
    @jwt_required()
    @require_roles("admin", "manager", "user")
    @require_scopes("posts:write")
    @user_owns_resource(param="id", allow_public_read=False)
    def delete_post(id: int):
        post: Post = g.target_post
        db.session.delete(post)
        db.session.commit()
        return "", 204

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
