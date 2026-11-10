from flask import Flask
from flask.views import MethodView
from flask_smorest import Api, Blueprint
from marshmallow import Schema, fields, validate

# 1. Khởi tạo App & cấu hình tự sinh Swagger UI / OpenAPI spec
app = Flask(__name__)
app.config["API_TITLE"] = "Demo Code-First API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config["OPENAPI_URL_PREFIX"] = "/"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/docs"
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

api = Api(app)

# Dữ liệu giả lập lưu trong RAM (không cần cài DB phức tạp)
PRODUCTS = [
    {"id": 1, "sku": "IPHONE-15", "name": "iPhone 15", "price_cents": 79900}
]

class ProductInSchema(Schema):
    sku = fields.Str(required=True, validate=validate.Length(min=3, max=32))
    name = fields.Str(required=True)
    price_cents = fields.Int(required=True, validate=validate.Range(min=0))

class ProductOutSchema(ProductInSchema):
    id = fields.Int(dump_only=True)

blp = Blueprint("products", __name__, url_prefix="/products", description="Quản lý sản phẩm")

@blp.route("")
class ProductList(MethodView):
    @blp.response(200, ProductOutSchema(many=True))
    def get(self):
        return PRODUCTS

    @blp.arguments(ProductInSchema)          # Tự validate input body & ghi vào spec
    @blp.response(201, ProductOutSchema)     # Tự format dữ liệu trả về & ghi vào spec
    def post(self, data):
        product = {"id": len(PRODUCTS) + 1, **data}
        PRODUCTS.append(product)
        return product

# Đăng ký Blueprint
api.register_blueprint(blp)

if __name__ == "__main__":
    print("Server dang chay tai: http://127.0.0.1:5000")

    app.run(debug=True, port=5000)
