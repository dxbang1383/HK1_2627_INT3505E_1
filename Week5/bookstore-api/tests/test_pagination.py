import pytest

from app import create_app
from models import Book, Category, db


@pytest.fixture()
def client():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )
    with app.app_context():
        category_fiction = Category(name="Fiction", slug="fiction")
        category_tech = Category(name="Technology", slug="technology")
        db.session.add_all([category_fiction, category_tech])
        db.session.flush()
        db.session.add_all(
            [
                Book(title="A", isbn="9780000000001", price_vnd=450000, stock=3, category=category_tech),
                Book(title="B", isbn="9780000000002", price_vnd=450000, stock=2, category=category_tech),
                Book(title="C", isbn="9780000000003", price_vnd=300000, stock=5, category=category_fiction),
                Book(title="D", isbn="9780000000004", price_vnd=200000, stock=1, category=category_fiction),
                Book(title="E", isbn="9780000000005", price_vnd=100000, stock=8, category=category_tech),
            ]
        )
        db.session.commit()
    with app.test_client() as test_client:
        yield test_client
    with app.app_context():
        db.drop_all()


def test_offset_pagination_returns_expected_metadata(client):
    response = client.get("/api/v1/books?strategy=offset&offset=1&limit=2")

    assert response.status_code == 200
    body = response.get_json()
    assert [book["id"] for book in body["data"]] == [2, 3]
    assert body["pagination"] == {
        "offset": 1,
        "limit": 2,
        "total": 5,
        "has_next": True,
    }


def test_cursor_default_is_descending_id_and_has_next_cursor(client):
    first = client.get("/api/v1/books?limit=2").get_json()

    assert [book["id"] for book in first["data"]] == [5, 4]
    assert first["page"]["has_more"] is True
    assert first["page"]["next"]

    second = client.get(
        "/api/v1/books?limit=2&cursor=" + first["page"]["next"]
    ).get_json()
    assert [book["id"] for book in second["data"]] == [3, 2]


def test_composite_cursor_does_not_skip_equal_sort_values(client):
    cursor = None
    received_ids = []
    while True:
        query = "/api/v1/books?strategy=cursor&limit=1&sort=-price"
        if cursor:
            query += "&cursor=" + cursor
        body = client.get(query).get_json()
        received_ids.extend(book["id"] for book in body["data"])
        if not body["page"]["has_more"]:
            break
        cursor = body["page"]["next"]

    assert received_ids == [2, 1, 3, 4, 5]
    assert len(received_ids) == len(set(received_ids))


def test_genre_filter_and_multi_key_sort(client):
    response = client.get(
        "/api/v1/books?strategy=offset&genre=technology&sort=-price,title"
    )

    assert response.status_code == 200
    body = response.get_json()
    assert [book["id"] for book in body["data"]] == [1, 2, 5]
    assert body["pagination"]["total"] == 3


@pytest.mark.parametrize(
    "query",
    [
        "?strategy=unknown",
        "?limit=101",
        "?offset=-1&strategy=offset",
        "?sort=-unknown",
        "?cursor=not-base64",
    ],
)
def test_invalid_pagination_parameters_return_400(client, query):
    assert client.get("/api/v1/books" + query).status_code == 400
