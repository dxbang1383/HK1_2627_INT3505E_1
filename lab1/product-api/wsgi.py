import sys
import os

# Đảm bảo thư mục src/ có thể được import đúng chuẩn
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from product_api.factory import create_app
from product_api.extensions import db

# Khởi tạo instance app
app = create_app()

# Tự động tạo bảng nếu chưa có (rất tiện lợi khi chạy Docker mới dựng)
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        app.logger.warning(f"Lưu ý tạo bảng: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
