from flask import Flask, jsonify, request

app = Flask(__name__)

BOOKS = [
    {"id": "abc-1234", "title": "Clean Code", "author": "R. Martin"},
    {"id": "def-5678", "title": "Learning Python", "author": "M. Lutz"},
    {"id": "ghi-9012", "title": "Fluent Python", "author": "L. Ramalho"},
]

def find_by_id(book_id):
    for book in BOOKS:
        if book["id"] == book_id:
            return book
    return None

@app.route("/books/<book_id>", methods=["GET"])
def get_book(book_id):
    book = find_by_id(book_id)
    if book is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(book), 200

@app.route("/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    return jsonify({"id": item_id}), 200

@app.route("/books", methods=["GET"])
def list_books():
    limit = int(request.args.get("limit", 20))
    q = request.args.get("q", "").strip().lower()

    items = []
    for book in BOOKS:
        if q in book["title"].lower():
            items.append(book)

    return jsonify({"items": items[:limit]}), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
