from flask import jsonify
from werkzeug.exceptions import HTTPException
from marshmallow import ValidationError

class ApiError(Exception):
    """Base exception cho toàn bộ lỗi business logic trong service."""
    status_code = 500
    code = "internal_error"

    def __init__(self, code=None, message="", status=None):
        super().__init__(message)
        if code:
            self.code = code
        if status:
            self.status_code = status
        self.message = message

class NotFound(ApiError):
    status_code = 404
    code = "not_found"

class Conflict(ApiError):
    status_code = 409
    code = "conflict"

class OutOfStock(ApiError):
    status_code = 409
    code = "out_of_stock"

def register_error_handlers(app):
    """Đăng ký global error handler cho ứng dụng Flask."""
    @app.errorhandler(ApiError)
    def _on_api(err):
        return jsonify({
            "code": err.code,
            "message": err.message or err.code,
        }), err.status_code

    @app.errorhandler(ValidationError)
    def _on_validation(err):
        return jsonify({
            "code": "validation_error",
            "message": "Dữ liệu yêu cầu không hợp lệ",
            "detail": err.messages,
        }), 422

    @app.errorhandler(HTTPException)
    def _on_http(err):
        return jsonify({
            "code": err.name.lower().replace(" ", "_"),
            "message": err.description,
        }), err.code

    @app.errorhandler(Exception)
    def _on_err(err):
        app.logger.exception("unhandled_exception")
        return jsonify({
            "code": "internal_error",
            "message": "Lỗi máy chủ nội bộ",
        }), 500
