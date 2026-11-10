from flask import Flask
from flask.views import MethodView
from flask_smorest import Api, Blueprint, abort
from marshmallow import Schema, fields, validate

# 1. Khởi tạo App & Cấu hình Swagger UI
app = Flask(__name__)
app.config["API_TITLE"] = "Demo Code-First API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config["OPENAPI_URL_PREFIX"] = "/"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/docs"  # Đường dẫn mở Swagger UI
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

api = Api(app)

# Dữ liệu giả lập lưu trong RAM
PRODUCTS = [
    {"id": 1, "sku": "IPHONE-15", "name": "iPhone 15", "price_cents": 79900},
    {"id": 2, "sku": "MACBOOK-M3", "name": "MacBook Air M3", "price_cents": 129900},
]

# 2. Định nghĩa Schemas
class ProductInSchema(Schema):
    """Schema dữ liệu client gửi lên (POST body)"""
    sku = fields.Str(required=True, validate=validate.Length(min=3, max=32))
    name = fields.Str(required=True)
    price_cents = fields.Int(required=True, validate=validate.Range(min=0))

class ProductOutSchema(ProductInSchema):
    """Schema dữ liệu server trả về (có thêm trường id)"""
    id = fields.Int(dump_only=True)

# 3. Tạo Blueprint
blp = Blueprint("products", __name__, url_prefix="/products", description="Quản lý sản phẩm")


# ─── ROUTE 1: /products (Xử lý trên cả danh sách) ───
@blp.route("")
class ProductList(MethodView):
    @blp.response(200, ProductOutSchema(many=True))
    def get(self):
        """Lấy danh sách tất cả sản phẩm"""
        return PRODUCTS

    @blp.arguments(ProductInSchema)
    @blp.response(201, ProductOutSchema)
    def post(self, data):
        """Tạo mới một sản phẩm"""
        product = {"id": len(PRODUCTS) + 1, **data}
        PRODUCTS.append(product)
        return product


# ─── ROUTE 2: /products/<id> (Xử lý trên 1 sản phẩm cụ thể) ───
@blp.route("/<int:product_id>")
class ProductDetail(MethodView):
    @blp.response(200, ProductOutSchema)
    def get(self, product_id):
        """Lấy thông tin chi tiết một sản phẩm theo ID"""
        for p in PRODUCTS:
            if p["id"] == product_id:
                return p
        abort(404, message="Không tìm thấy sản phẩm có ID này!")

    @blp.response(204)
    def delete(self, product_id):
        """Xóa một sản phẩm theo ID"""
        global PRODUCTS
        for i, p in enumerate(PRODUCTS):
            if p["id"] == product_id:
                PRODUCTS.pop(i)
                return ""  # 204 No Content
        abort(404, message="Không tìm thấy sản phẩm để xóa!")


# Đăng ký Blueprint vào API
api.register_blueprint(blp)

if __name__ == "__main__":
    print("------------------------------------------------------------------")
    print("Server dang chay tai: http://127.0.0.1:5000")
    print("-> Xem Swagger UI tu sinh tai: http://127.0.0.1:5000/docs")
    print("-> Xem file OpenAPI spec tu sinh tai: http://127.0.0.1:5000/openapi.json")
    print("------------------------------------------------------------------")
    app.run(debug=True, port=5000)
