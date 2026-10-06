import logging
import uuid

from flask import jsonify, request
from werkzeug.exceptions import HTTPException

log = logging.getLogger(__name__)
ERROR_BASE = "https://api.example.com/probs"


class ProblemError(Exception):
    def __init__(self, status, title, detail=None, type_path=None, **extra):
        super().__init__(title)
        self.status = status
        self.title = title
        self.detail = detail
        self.type_path = type_path
        self.extra = extra


def _problem(status, title, detail=None, type_path=None, **extra):
    body = {
        "type": f"{ERROR_BASE}/{type_path}" if type_path else "about:blank",
        "title": title,
        "status": status,
        "instance": request.path,
        "trace_id": str(uuid.uuid4()),
    }
    if detail:
        body["detail"] = detail
    body.update(extra)

    resp = jsonify(body)
    resp.status_code = status
    resp.headers["Content-Type"] = "application/problem+json"
    return resp


def register_error_handlers(app):
    @app.errorhandler(ProblemError)
    def handle_problem(e):
        return _problem(e.status, e.title, e.detail, e.type_path, **e.extra)

    @app.errorhandler(HTTPException)
    def handle_http(e):
        return _problem(e.code, e.name, e.description)

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        log.exception("Unhandled exception at %s", request.path)
        return _problem(500, "Internal Server Error",
                        "Đã xảy ra lỗi không mong muốn.", "internal-error")