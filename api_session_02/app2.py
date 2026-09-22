from flask import Flask, jsonify, request, make_response

app = Flask(__name__)

BOOKS = [
    { "id": 0, "title": "Bang1383", "author": "dxbang1383" }
]

@app.route("/books", methods=["GET"]) 
def list_book():
    return jsonify({
        "data": BOOKS, 
        "total": len(BOOKS)
    }), 200

# cache 60s
@app.get("/books/<int:bid>")
def fetch(bid):
    i = next(
        (k for k, b in enumerate(BOOKS) if b["id"] == bid),
        None
    )

    if i is None:
        return jsonify(error="not found"), 404

    resp = make_response(jsonify(BOOKS[i]), 200)
    resp.headers["Cache-Control"] = "max-age=60"

    return resp

# thay toàn bộ, title + author bắt buộc
@app.put("/books/<int:bid>")
def put(bid):
    i = next(
        (k for k, b in enumerate(BOOKS) if b["id"] == bid),
        None
    )

    if i is None:
        return jsonify(error="not found"), 404

    p = request.get_json(silent=True) or {}

    t = p.get("title")
    a = p.get("author")

    if not t or not a:
        return jsonify(error="need title+author"), 422

    BOOKS[i] = {
        "id": bid,
        "title": t.strip(),
        "author": a.strip(),
        "isbn": p.get("isbn"),
        "price": p.get("price")
    }

    return jsonify(BOOKS[i]), 200

# chỉ cập nhật field có trong body
@app.patch("/books/<int:bid>")
def patch(bid):
    i = next(
        (k for k, b in enumerate(BOOKS) if b["id"] == bid),
        None
    )

    if i is None:
        return jsonify(error="not found"), 404

    p = request.get_json(silent=True) or {}

    if p.get("price", 0) < 0:
        return jsonify(error="price must be positive"), 422

    for k in "title author isbn price".split():
        if k in p:
            BOOKS[i][k] = p[k]

    return jsonify(BOOKS[i]), 200

# idempotent, trả 204
@app.delete("/books/<int:bid>")
def delete(bid):
    i = next(
        (k for k, b in enumerate(BOOKS) if b["id"] == bid),
        None
    )

    if i is None:
        return jsonify(error="not found"), 404

    BOOKS.pop(i)

    return "", 204


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )