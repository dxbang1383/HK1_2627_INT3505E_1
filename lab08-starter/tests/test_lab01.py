"""LAB 1 — add your five tests here. Do not delete the smoke tests.

A. GET /books, empty database -> HTTP 200 and []
B. GET /books/9999 -> HTTP 404, JSON code == NOT_FOUND
C. POST /books with only author -> HTTP 400, errors contains title
D. POST valid book, DELETE it, GET same id -> HTTP 404
BONUS. Validate a Book response using JSON Schema; add an unknown
       field to a *copy* of the response and assert ValidationError.

Useful imports:
    from jsonschema import validate, ValidationError
    import pytest
    from tools import get_book_schema

Do not depend on test execution order. Fixtures: client, app, sample_book.
"""

def test_get_books_empty_db(client):
    response = client.get("/books")
    assert response.status_code == 200
    assert response.get_json() == []

def test_get_book_9999(client):
    response = client.get("/books/9999")
    assert response.status_code == 404
    data = response.get_json()
    assert data["code"] == "NOT_FOUND"

def test_post_with_only_author(client):
    response = client.post("/books", json={"author": "bang1383"})
    assert response.status_code == 400
    data = response.get_json()
    assert any(err.get("field") == "title" for err in data["errors"])

def test_delete_book_then_get_404(client):
    create_resp = client.post(
        "/books",
        json={"title": "Clean Code", "author": "bang1383"},
    )
    assert create_resp.status_code == 201
    book_id = create_resp.get_json()["id"]

    delete_resp = client.delete(f"/books/{book_id}")
    assert delete_resp.status_code == 204

    get_resp = client.get(f"/books/{book_id}")
    assert get_resp.status_code == 404

