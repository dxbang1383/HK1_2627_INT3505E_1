from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models.product import Product
from ..errors import Conflict, NotFound, OutOfStock
from ..schemas.product import ProductOut, ProductIn, ProductPatch, ReserveIn

# Khởi tạo Blueprint với tiền tố URL: /api/v1/products
products_bp = Blueprint("products", __name__, url_prefix="/api/v1/products")


# ─── 1. GET /api/v1/products (Lấy danh sách có phân trang) ───
@products_bp.get("")
def list_products():
    page = max(1, int(request.args.get("page", 1)))
    size = min(100, max(1, int(request.args.get("size", 20))))

    # Chỉ lấy các sản phẩm chưa bị xóa mềm (archived = False)
    base = db.select(Product).where(Product.archived.is_(False))

    rows = db.session.execute(
        base.order_by(Product.id)
        .offset((page - 1) * size)
        .limit(size)
    ).scalars().all()

    total = db.session.scalar(
        db.select(db.func.count())
        .select_from(Product)
        .where(Product.archived.is_(False))
    )

    return jsonify({
        "items": [ProductOut().dump(p) for p in rows],
        "page": page,
        "size": size,
        "total": total,
    }), 200


# ─── 2. GET /api/v1/products/<int:id> (Lấy 1 sản phẩm chi tiết) ───
@products_bp.get("/<int:id>")
def get_product(id):
    p = db.session.get(Product, id)
    if p is None or p.archived:
        raise NotFound(message="Không tìm thấy sản phẩm")
    return jsonify(ProductOut().dump(p)), 200


# ─── 3. POST /api/v1/products (Tạo sản phẩm mới) ───
@products_bp.post("")
def create_product():
    # Marshmallow tự kiểm tra kiểu dữ liệu và rule
    body = ProductIn().load(request.json or {})
    p = Product(**body)
    db.session.add(p)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()  # Quan trọng: rollback khi vi phạm unique SKU
        raise Conflict(message="SKU đã tồn tại trong hệ thống")
    return jsonify(ProductOut().dump(p)), 201


# ─── 4. POST /api/v1/products/<int:id>/reserve (Đặt trước / giảm kho) ───
@products_bp.post("/<int:id>/reserve")
def reserve_product(id):
    body = ReserveIn().load(request.json or {})
    qty = body["qty"]

    p = db.session.get(Product, id)
    if p is None or p.archived:
        raise NotFound(message="Không tìm thấy sản phẩm")

    if p.qty_in_stock < qty:
        raise OutOfStock(message=f"Chỉ còn {p.qty_in_stock} sản phẩm trong kho")

    p.qty_in_stock -= qty
    db.session.commit()
    return jsonify(ProductOut().dump(p)), 200


# ─── 5. PATCH /api/v1/products/<int:id> (Cập nhật một phần) ───
@products_bp.patch("/<int:id>")
def patch_product(id):
    body = ProductPatch().load(request.json or {}, partial=True)
    p = db.session.get(Product, id)
    if p is None or p.archived:
        raise NotFound(message="Không tìm thấy sản phẩm")

    # Chỉ cập nhật các trường có gửi lên trong request body
    for key, value in body.items():
        setattr(p, key, value)

    db.session.commit()
    return jsonify(ProductOut().dump(p)), 200


# ─── 6. DELETE /api/v1/products/<int:id> (Xóa mềm - soft delete) ───
@products_bp.delete("/<int:id>")
def delete_product(id):
    p = db.session.get(Product, id)
    if p is None or p.archived:
        raise NotFound(message="Không tìm thấy sản phẩm")

    p.archived = True  # Đánh dấu đã xóa, không xóa vật lý khỏi database
    db.session.commit()
    return "", 204
