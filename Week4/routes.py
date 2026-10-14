
from flask import Blueprint, jsonify, request

from . import services
from .schemas import (
    parse_author_payload,
    parse_book_payload,
    parse_borrow_payload,
)

api_bp = Blueprint("api", __name__)

BOOK_FIELDS = ("title", "author", "published_year")
AUTHOR_FIELDS = ("name",)
BORROW_FIELDS = ("book_id", "borrower")


def error(message, status_code):
    return jsonify({"error": message}), status_code


def parse_payload(parser, required_fields):
    payload, validation_error = parser(required_fields)
    if validation_error:
        status_code = 415 if not request.is_json else 400
        return None, error(validation_error, status_code)
    return payload, None


def list_response(items):
    return jsonify({"data": items, "total": len(items)}), 200


@api_bp.get("/")
def index():
    return jsonify({"message": "Book Management API", "books_endpoint": "/books"})


@api_bp.get("/books")
def list_books():
    return list_response(services.list_books())


@api_bp.get("/books/<int:book_id>")
def get_book(book_id):
    book = services.get_book(book_id)
    if book is None:
        return error("Book not found", 404)
    return jsonify(book), 200


@api_bp.post("/books")
def create_book():
    payload, validation_response = parse_payload(parse_book_payload, BOOK_FIELDS)
    if validation_response:
        return validation_response

    book = services.create_book(payload)
    return jsonify(book), 201


@api_bp.put("/books/<int:book_id>")
def update_book(book_id):
    payload, validation_response = parse_payload(parse_book_payload, BOOK_FIELDS)
    if validation_response:
        return validation_response

    book = services.update_book(book_id, payload)
    if book is None:
        return error("Book not found", 404)
    return jsonify(book), 200


@api_bp.delete("/books/<int:book_id>")
def delete_book(book_id):
    if not services.delete_book(book_id):
        return error("Book not found", 404)
    return "", 204


@api_bp.get("/authors")
def list_authors():
    return list_response(services.list_authors())


@api_bp.get("/authors/<int:author_id>")
def get_author(author_id):
    author = services.get_author(author_id)
    if author is None:
        return error("Author not found", 404)
    return jsonify(author), 200


@api_bp.post("/authors")
def create_author():
    payload, validation_response = parse_payload(
        parse_author_payload, AUTHOR_FIELDS
    )
    if validation_response:
        return validation_response
    return jsonify(services.create_author(payload)), 201


@api_bp.put("/authors/<int:author_id>")
def update_author(author_id):
    payload, validation_response = parse_payload(
        parse_author_payload, AUTHOR_FIELDS
    )
    if validation_response:
        return validation_response

    author = services.update_author(author_id, payload)
    if author is None:
        return error("Author not found", 404)
    return jsonify(author), 200


@api_bp.delete("/authors/<int:author_id>")
def delete_author(author_id):
    if not services.delete_author(author_id):
        return error("Author not found", 404)
    return "", 204


@api_bp.get("/borrows")
def list_borrows():
    return list_response(services.list_borrows())


@api_bp.get("/borrows/<int:borrow_id>")
def get_borrow(borrow_id):
    borrow = services.get_borrow(borrow_id)
    if borrow is None:
        return error("Borrow record not found", 404)
    return jsonify(borrow), 200


@api_bp.post("/borrows")
def create_borrow():
    payload, validation_response = parse_payload(
        parse_borrow_payload, BORROW_FIELDS
    )
    if validation_response:
        return validation_response
    return jsonify(services.create_borrow(payload)), 201


@api_bp.put("/borrows/<int:borrow_id>")
def update_borrow(borrow_id):
    payload, validation_response = parse_payload(
        parse_borrow_payload, BORROW_FIELDS
    )
    if validation_response:
        return validation_response

    borrow = services.update_borrow(borrow_id, payload)
    if borrow is None:
        return error("Borrow record not found", 404)
    return jsonify(borrow), 200


@api_bp.delete("/borrows/<int:borrow_id>")
def delete_borrow(borrow_id):
    if not services.delete_borrow(borrow_id):
        return error("Borrow record not found", 404)
    return "", 204
