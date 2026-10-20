from flask import Flask, jsonify

from models import db
from routes.books import books_bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI="sqlite:///bookstore.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    app.register_blueprint(books_bp, url_prefix="/api/v1")

    @app.get("/")
    def health_check():
        return jsonify({"service": "Bookstore API", "status": "ok"})

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
