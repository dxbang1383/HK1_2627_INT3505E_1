import uuid
from flask import Flask, jsonify, request

app = Flask(__name__)

# Bộ nhớ tạm lưu trữ danh sách tasks (Key là id của task)
tasks = {
    "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d": {
        "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
        "title": "Học thiết kế API tuần 4",
        "status": "todo",
        "priority": "medium",
        "dueDate": "2026-10-20T23:59:59Z",
        "assigneeId": "c73bcdcc-2669-4bf6-81d3-e4ae73fb11fd"
    }
}

# 1. GET /tasks: Lấy danh sách tất cả các task
@app.get("/tasks")
def get_tasks():
    return jsonify(list(tasks.values())), 200

# 2. POST /tasks: Tạo một task mới
@app.post("/tasks")
def create_task():
    data = request.get_json() or {}
    
    # Kiểm tra trường bắt buộc
    if not data.get("title"):
        return jsonify({"message": "Trường 'title' là bắt buộc"}), 400

    task_id = str(uuid.uuid4())
    new_task = {
        "id": task_id,
        "title": data["title"],
        "status": data.get("status", "todo"),
        "priority": data.get("priority", "medium"),
        "dueDate": data.get("dueDate"),
        "assigneeId": data.get("assigneeId")
    }
    
    tasks[task_id] = new_task
    return jsonify(new_task), 201

# 3. GET /tasks/<taskId>: Lấy chi tiết task theo id
@app.get("/tasks/<task_id>")
def get_task_by_id(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({"message": "Không tìm thấy task"}), 404
    return jsonify(task), 200

# 4. PATCH /tasks/<taskId>: Cập nhật thông tin task
@app.patch("/tasks/<task_id>")
def patch_task(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({"message": "Không tìm thấy task"}), 404

    data = request.get_json() or {}
    
    # Cập nhật các trường được gửi lên
    for field in ["title", "status", "priority", "dueDate", "assigneeId"]:
        if field in data:
            task[field] = data[field]

    return jsonify(task), 200

# 5. DELETE /tasks/<taskId>: Xóa task (204 No Content)
@app.delete("/tasks/<task_id>")
def delete_task(task_id):
    if task_id not in tasks:
        return jsonify({"message": "Không tìm thấy task"}), 404
        
    del tasks[task_id]
    return "", 204

if __name__ == "__main__":
    app.run(debug=True, port=5000)
