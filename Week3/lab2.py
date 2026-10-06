from flask import Flask, jsonify
from error2 import ProblemError, register_error_handlers

app = Flask(__name__)
register_error_handlers(app)

USERS = {1: "Alice", 2: "Bob"}


@app.get("/users/<int:id>")
def get_user(id):
    if id not in USERS:
        raise ProblemError(404, "User not found",
                           detail=f"Không tìm thấy user với id {id}",
                           type_path="user-not-found",
                           resource_id=id)
    return jsonify({"id": id, "name": USERS[id]})

if __name__ == "__main__":
    app.run(debug=False)