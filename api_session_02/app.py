from flask import Flask, jsonify, request, make_response

app = Flask(__name__)

BOOKS = [
    {"id": 0 , "title": "Bang1383", "author" : "dxbang1383"}

]
_next_id = 1

# ——— GET /books ——— trả danh sách
@app.get("/books")
def list_books():
    return jsonify({
        "data": BOOKS,
        "total": len(BOOKS)
    }), 200

# ——— POST /books ——— tạo mới
@app.post("/books")
def create_book():
    global _next_id

    # Kiểm tra Content-Type phải là application/json
    if not request.is_json:
        return jsonify(error="Content-Type must be application/json"), 415

    p = request.get_json(silent=True)

    # JSON không parse được (body rỗng / sai cú pháp)
    if p is None:
        return jsonify(error="expected JSON"), 400

    t = (p.get("title") or "").strip()
    a = (p.get("author") or "").strip()

    # Thiếu title hoặc author
    if not t or not a:
        return jsonify(error="title and author required"), 422

    book = {"id": _next_id, "title": t, "author": a}
    BOOKS.append(book)
    _next_id += 1

    resp = make_response(jsonify(book), 201)
    resp.headers["Location"] = f"/books/{book['id']}"
    return resp


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
