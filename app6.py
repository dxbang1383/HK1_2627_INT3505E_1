from flask import Flask, jsonify, request

app = Flask(__name__)

BOOKS = [
    {"id": 1, "title": "Clean Code", "author": "R. Martin"},
    {"id": 2, "title": "Pragmatic Programmer", "author": "Hunt & Thomas"},
]
next_id = 3

def find(bid):
    for book in BOOKS:
        if book["id"] == bid:
            return book
    return None

@app.route("/books", methods=["GET"])
def list_books():
    limit = request.args.get("limit", 100, type=int)
    return jsonify(BOOKS[:limit]), 200

@app.route("/books/<int:bid>", methods=["GET"])
def get_book(bid):
    book = find(bid)
    if book is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(book), 200

@app.route("/books", methods=["POST"])
def create_book():
    global next_id
    body = request.get_json(silent=True) or {}
    title = body.get("title")
    author = body.get("author")
    if not title or not author:
        return jsonify({"error": "title+author required"}), 400

    book = {"id": next_id, "title": title, "author": author}
    next_id += 1
    BOOKS.append(book)
    return jsonify(book), 201, {"Location": f"/books/{book['id']}"}

@app.route("/books/<int:bid>", methods=["PUT"])
def update_book(bid):
    book = find(bid)
    if book is None:
        return jsonify({"error": "not found"}), 404

    body = request.get_json(silent=True) or {}
    body.pop("id", None)
    book.update(body)
    return jsonify(book), 200

@app.route("/books/<int:bid>", methods=["DELETE"])
def delete_book(bid):
    book = find(bid)
    if book is None:
        return jsonify({"error": "not found"}), 404

    BOOKS.remove(book)
    return "", 204

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
