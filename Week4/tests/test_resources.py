import pytest

from app import create_app
from app.services import reset_all


@pytest.fixture()
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as test_client:
        reset_all()
        yield test_client
        reset_all()


def test_author_routes_accept_nullable_bio(client):
    response = client.post("/authors", json={"name": "test1", "bio": None})

    assert response.status_code == 201
    assert response.get_json() == {
        "id": 1,
        "name": "test1",
        "bio": "",
    }
    assert client.get("/authors/1").status_code == 200


def test_borrow_routes_default_nullable_status(client):
    response = client.post(
        "/borrows",
        json={"book_id": 1, "borrower": "Ada", "status": None},
    )

    assert response.status_code == 201
    assert response.get_json() == {
        "id": 1,
        "book_id": 1,
        "borrower": "Ada",
        "status": "borrowed",
        "borrow_date": None,
    }
    assert client.get("/borrows").get_json()["total"] == 1


def test_invalid_content_type_returns_415(client):
    response = client.post("/authors", data="name=Ada")

    assert response.status_code == 415
    assert "error" in response.get_json()