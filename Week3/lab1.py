from flask import Flask, jsonify, request

app = Flask(__name__)

USERS = [
    {"id": 1, "name": "user1"},
    {"id": 2, "name": "user2"}
]

POSTS = [
    {"id": 1, "title": "post1", "user_id": 1},
    {"id": 2, "title": "post2", "user_id": 2}
]

COMMENTS = [
    {"id": 1, "content": "comment1", "post_id": 1, "user_id": 1},
    {"id": 2, "content": "comment2", "post_id": 1, "user_id": 2},
    {"id": 3, "content": "comment3", "post_id": 2, "user_id": 1}
]

TAGS = [
    {"id": 1, "name": "tag1"},
    {"id": 2, "name": "tag2"}
]

FOLLOWS = [
    {"follower_id": 1, "following_id": 2},
    {"follower_id": 2, "following_id": 1}
]
next_post_id = 2


def find_post(post_id):
    for post in POSTS:
        if post["id"] == post_id:
            return post
    return None


@app.route("/api/v1/posts", methods=["GET"])
def list_posts():
    limit = request.args.get("limit", default=20, type=int)
    return jsonify({"items": POSTS[:limit]}), 200

@app.route("/api/v1/users", method=["GET"])
#
@app.route("/api/v1/users/<int:user_id>/posts", method = ["GET"])
#
@app.route("/api/v1/users/<int:user_id>/follows", method = ["GET"])
def a():
    return 
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
