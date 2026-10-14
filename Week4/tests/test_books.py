import pytest

from app import create_app
from app.services import reset_books


@pytest.fixture()
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as test_client:
        reset_books()
        yield test_client
        reset_books()


def sample_book():
    return {
        "title": "Clean Code",
        "author": "zzzzz",
        "published_year": 2008,
    }


def test_list_books_initially_empty(client):
    response = client.get("/books")
    assert response.status_code == 200
    assert response.get_json() == {"data": [], "total": 0}


def test_create_and_get_book(client):
    response = client.post("/books", json=sample_book())
    assert response.status_code == 201
    created = response.get_json()
    assert created["id"] == 1
    assert created["title"] == "Clean Code"

    response = client.get("/books/1")
    assert response.status_code == 200
    assert response.get_json() == created


def test_create_requires_all_fields(client):
    response = client.post("/books", json={"title": "Only a title"})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_update_book(client):
    client.post("/books", json=sample_book())
    updated = {
        "title": "Clean Code2",
        "author": "zzzzz",
        "published_year": 2009,
    }

    response = client.put("/books/1", json=updated)
    assert response.status_code == 200
    assert response.get_json()["title"] == "Clean Code2"


def test_delete_book(client):
    client.post("/books", json=sample_book())

    response = client.delete("/books/1")
    assert response.status_code == 204

    response = client.get("/books/1")
    assert response.status_code == 404


def test_unknown_book_returns_404(client):
    response = client.get("/books/999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Book not found"}