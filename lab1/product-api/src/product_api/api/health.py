from flask import Blueprint, jsonify
from sqlalchemy import text
from ..extensions import db

health_bp = Blueprint("health", __name__, url_prefix="")


# ─── 1. Liveness Probe (Kiểm tra tiến trình còn sống không) ───
@health_bp.get("/healthz")
def liveness():
    """
    Liveness probe: Trọng lượng nhẹ, không phụ thuộc vào Database.
    Trả về 200 ngay lập tức nếu tiến trình Flask còn đang chạy.
    """
    return jsonify({"status": "ok"}), 200


# ─── 2. Readiness Probe (Kiểm tra hệ thống sẵn sàng nhận traffic chưa) ───
@health_bp.get("/ready")
def readiness():
    """
    Readiness probe: Kiểm tra các dependency thiết yếu (Database).
    Thực hiện truy vấn SELECT 1 nhẹ nhàng.
    - Trả về 200 nếu kết nối Database bình thường.
    - Trả về 503 nếu mất kết nối Database (hệ thống degraded).
    """
    checks = {}
    try:
        db.session.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception:
        checks["db"] = "err"

    is_all_ok = all(v == "ok" for v in checks.values())
    status_text = "ok" if is_all_ok else "degraded"
    status_code = 200 if is_all_ok else 503

    return jsonify({
        "status": status_text,
        "checks": checks
    }), status_code
