import os
from flask import Flask
from .extensions import db, migrate
from .config import DefaultConfig
from .errors import register_error_handlers
from .api.products import products_bp
from .api.health import health_bp

def create_app(config=None):
    """
    Application Factory (Slide 13 & 16):
    Khởi tạo Flask app, nạp cấu hình, kết nối database và đăng ký các Blueprint.
    """
    cfg = config or os.environ.get("APP_CONFIG", DefaultConfig)
    app = Flask(__name__)
    app.config.from_object(cfg)

    # Khởi tạo các tiện ích mở rộng (extensions)
    db.init_app(app)
    migrate.init_app(app, db)

    # Đăng ký bộ xử lý lỗi tập trung
    register_error_handlers(app)

    # Đăng ký các Blueprint
    app.register_blueprint(products_bp)
    app.register_blueprint(health_bp)

    return app
