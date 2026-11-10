from marshmallow import Schema, fields, validate

# ─── 1. Output Schema (trả về client) ───
class ProductOut(Schema):
    """Schema dùng để serialize dữ liệu sản phẩm gửi về cho client."""
    id = fields.Int()
    sku = fields.Str()
    name = fields.Str()
    description = fields.Str(allow_none=True)
    price_cents = fields.Int()
    qty_in_stock = fields.Int()
    archived = fields.Bool()

# ─── 2. Input Schema (tạo mới sản phẩm) ───
class ProductIn(Schema):
    """Schema kiểm tra dữ liệu gửi lên khi tạo sản phẩm (POST)."""
    sku = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=32)
    )
    name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=255)
    )
    description = fields.Str(allow_none=True, load_default=None)
    price_cents = fields.Int(
        required=True,
        validate=validate.Range(min=0)
    )
    qty_in_stock = fields.Int(
        load_default=0,
        validate=validate.Range(min=0)
    )

# ─── 3. Patch Schema (cập nhật 1 phần) ───
class ProductPatch(Schema):
    """Schema dùng cho API cập nhật từng phần (PATCH)."""
    name = fields.Str(validate=validate.Length(min=1, max=255))
    description = fields.Str(allow_none=True)
    price_cents = fields.Int(validate=validate.Range(min=0))
    qty_in_stock = fields.Int(validate=validate.Range(min=0))

# ─── 4. Reserve Schema (đặt trước) ───
class ReserveIn(Schema):
    """Schema dùng cho API đặt trước hàng /reserve."""
    qty = fields.Int(
        required=True,
        validate=validate.Range(min=1)
    )
