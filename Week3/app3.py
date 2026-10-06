import base64
import json
 
from flask import Flask, jsonify, request
 
from error2 import ProblemError, register_error_handlers
 
app = Flask(__name__)
register_error_handlers(app)
 
ORDERS = [
    {"id": 1, "customer_id": 101, "status": "paid", "total": 150.0, "created_at": "2026-01-01"},
    {"id": 2, "customer_id": 102, "status": "pending", "total": 80.0, "created_at": "2026-01-02"},
    {"id": 3, "customer_id": 101, "status": "paid", "total": 200.0, "created_at": "2026-01-03"},
    {"id": 4, "customer_id": 103, "status": "cancelled", "total": 45.0, "created_at": "2026-01-04"},
    {"id": 5, "customer_id": 101, "status": "paid", "total": 310.0, "created_at": "2026-01-05"},
    {"id": 6, "customer_id": 102, "status": "paid", "total": 120.0, "created_at": "2026-01-06"},
]
 
ALL_FIELDS = set(ORDERS[0].keys())
SORTABLE = {"id", "created_at", "total"}
DEFAULT_LIMIT, MAX_LIMIT = 2, 100
 
# ---------- Cursor: base64(json) ----------
def encode_cursor(sort_field, desc, last):
    data = {"f": sort_field, "d": desc, "v": last[sort_field], "id": last["id"]}
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode()
 
 
def decode_cursor(token, sort_field, desc):
    try:
        data = json.loads(base64.urlsafe_b64decode(token.encode()))
        if data["f"] != sort_field or data["d"] != desc:
            raise ValueError("cursor không khớp với sort hiện tại")
        return data["v"], data["id"]
    except Exception:
        raise ProblemError(400, "Invalid cursor",
                           detail="Cursor không hợp lệ hoặc không khớp với tham số sort.",
                           type_path="invalid-cursor")
 
 
def parse_limit():
    raw = request.args.get("limit", DEFAULT_LIMIT)
    try:
        limit = int(raw)
        if not 1 <= limit <= MAX_LIMIT:
            raise ValueError
    except ValueError:
        raise ProblemError(400, "Invalid limit",
                           detail=f"limit phải là số nguyên từ 1 đến {MAX_LIMIT}.",
                           type_path="invalid-parameter")
    return limit
 
 
# ---------- GET /orders ----------
@app.get("/orders")
def list_orders():
    limit = parse_limit()
 
    # (2) Filtering
    items = ORDERS
    status = request.args.get("status")
    if status:
        items = [o for o in items if o["status"] == status]
    customer_id = request.args.get("customer_id")
    if customer_id:
        try:
            cid = int(customer_id)
        except ValueError:
            raise ProblemError(400, "Invalid customer_id",
                               detail="customer_id phải là số nguyên.",
                               type_path="invalid-parameter")
        items = [o for o in items if o["customer_id"] == cid]
 
    # (3) Sorting: sort=created_at (tăng) hoặc sort=-created_at (giảm)
    sort = request.args.get("sort", "id")
    desc = sort.startswith("-")
    sort_field = sort.lstrip("-")
    if sort_field not in SORTABLE:
        raise ProblemError(400, "Invalid sort field",
                           detail=f"sort phải thuộc: {', '.join(sorted(SORTABLE))}.",
                           type_path="invalid-parameter")
    # Thêm id làm tie-breaker để thứ tự luôn ổn định
    key = lambda o: (o[sort_field], o["id"])
    items = sorted(items, key=key, reverse=desc)
 
    # (1) Cursor pagination (keyset): lấy các bản ghi nằm sau điểm mốc
    token = request.args.get("cursor")
    if token:
        v, last_id = decode_cursor(token, sort_field, desc)
        after = (v, last_id)
        items = [o for o in items if (key(o) < after if desc else key(o) > after)]
 
    page = items[:limit]
    next_cursor = encode_cursor(sort_field, desc, page[-1]) if len(items) > limit else None
 
    # (4) Sparse fieldsets: fields=id,total
    fields = request.args.get("fields")
    if fields:
        wanted = [f.strip() for f in fields.split(",") if f.strip()]
        unknown = [f for f in wanted if f not in ALL_FIELDS]
        if unknown:
            raise ProblemError(400, "Invalid fields",
                               detail=f"Trường không tồn tại: {', '.join(unknown)}.",
                               type_path="invalid-parameter")
        page = [{f: o[f] for f in wanted} for o in page]
 
    return jsonify({"data": page, "limit": limit, "next_cursor": next_cursor})
 
if __name__ == "__main__":
    app.run(debug=False)