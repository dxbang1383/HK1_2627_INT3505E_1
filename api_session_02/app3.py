from flask import Flask, jsonify, request, make_response

app = Flask(__name__)

DEFAULT_SIZE = 20
MAX_SIZE = 100

BOOKS = [
    {"id": 1, "title": "Clean Code", "author": "Robert Martin"},
    {"id": 2, "title": "Clean Architecture", "author": "Robert Martin"},
    {"id": 3, "title": "The Pragmatic Programmer", "author": "David Thomas"},
    {"id": 4, "title": "1984", "author": "Orwell"},
    {"id": 5, "title": "Animal Farm", "author": "Orwell"},
    {"id": 6, "title": "Python Crash Course", "author": "Eric Matthes"},
    {"id": 7, "title": "Fluent Python", "author": "Luciano Ramalho"},
    {"id": 8, "title": "Effective Python", "author": "Brett Slatkin"},
    {"id": 9, "title": "Learning Python", "author": "Mark Lutz"},
    {"id": 10, "title": "Django for APIs", "author": "William Vincent"},
    {"id": 11, "title": "Clean Code Guide", "author": "Orwell"},
    {"id": 12, "title": "Clean Arch", "author": "Orwell"},
]


# =========================================================
# GET /books
# Pagination + Filtering + HATEOAS + Cache-Control
# =========================================================

@app.get("/books")
def list_books():

    try:
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", DEFAULT_SIZE))

    except ValueError:
        return jsonify(
            error="page and size must be int"
        ), 400

    page = max(page, 1)

    size = max(min(size, MAX_SIZE), 1)

    # Lọc author chính xác
    author = request.args.get("author")

    filtered = BOOKS

    if author:
        filtered = [
            b for b in filtered
            if b["author"].lower() == author.lower()
        ]

    # Tìm q trong title
    q = request.args.get("q", "").lower()

    if q:
        filtered = [
            b for b in filtered
            if q in b["title"].lower()
        ]

    total = len(filtered)

    start = (page - 1) * size
    end = start + size

    items = filtered[start:end]

    # Số trang
    total_pages = (total + size - 1) // size

    # Nếu không có dữ liệu thì vẫn coi là 1 page
    last = max(total_pages, 1)

    def url(p):
        return f"/books?page={p}&size={size}"

    links = {
        "self": {
            "href": url(page)
        },

        "first": {
            "href": url(1)
        },

        "last": {
            "href": url(last)
        }
    }

    # Có trang trước
    if page > 1:
        links["prev"] = {
            "href": url(page - 1)
        }

    # Có trang sau
    if page < total_pages:
        links["next"] = {
            "href": url(page + 1)
        }

    body = {
        "data": items,

        "pagination": {
            "page": page,
            "size": size,
            "total": total,
            "total_pages": total_pages,
            "last": last
        },

        "links": links
    }

    resp = make_response(
        jsonify(body),
        200
    )

    # Cache trong 30 giây
    resp.headers["Cache-Control"] = "public, max-age=30"

    return resp

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )