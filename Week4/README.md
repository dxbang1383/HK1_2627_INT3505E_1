# Task API - Book Management

## Thông tin nhóm

| Họ và tên | MSSV | Vai trò |
|---|---:|---|
| Tô Đức Anh | 24021375 | Viết Schema |
| Nguyễn Thế Nhân | 24020257 |Viết OpenAPI  |
| Ngô Quang Dũng | 24020086 | Viết services |
| Đỗ Xuân Bằng | 24021383 |Viết test và routes |
| Lại Quang Hải | 24021455 |Viết OpenAPI |

**Nhóm 3 — Lớp học phần: INT3505E 1 (Kiến trúc hướng dịch vụ)**

## Tính năng chính

| Module | Mô tả |
|---|---|
| Books | Quản lý thông tin sách, bao gồm thêm, xem, cập nhật và xóa dữ liệu sách. |
| Authors | Quản lý thông tin tác giả liên kết với sách. |
| Borrows | Quản lý phiếu mượn sách của người mượn. |
| OpenAPI Spec | Mô tả contract API bằng file YAML, có thể tích hợp với Swagger / Redocly. |
| Validation | Kiểm tra dữ liệu đầu vào và trả về lỗi theo chuẩn HTTP. |

### Điểm kỹ thuật nổi bật

- Xây dựng API theo mô hình RESTful với Flask.
- Tách rõ logic nghiệp vụ trong `services.py` và xử lý request trong `routes.py`.
- Sử dụng OpenAPI YAML để định nghĩa API rõ ràng, dễ mở rộng và kiểm thử.
- Dùng cấu trúc module hóa: `books`, `authors`, `borrows` với schema dùng chung.
- Hỗ trợ xử lý lỗi chuẩn hóa và phản hồi JSON đồng nhất.
- Có bộ kiểm thử tự động bằng `pytest` để xác thực hành vi API.

## Swagger UI

Sau khi chạy Flask, mở [Swagger UI](http://127.0.0.1:5000/docs) để xem tài liệu và thử gọi API. Đặc tả JSON được cung cấp tại [OpenAPI JSON](http://127.0.0.1:5000/openapi.json); Swagger UI bật sẵn **Try it out** và dùng host hiện tại của ứng dụng.

Ảnh minh chứng Swagger UI với **Try it out**:
**Books**
![Swagger UI - Try it out](task-api/swagger-ui-1.png)
**Authors**
![Swagger UI - Try it out](task-api/swagger-ui-2.png)
**Borrow**
![Swagger UI - Try it out](task-api/swagger-ui-3.png)


## Hai quyết định thiết kế khó nhất

1. **Duy trì OpenAPI theo YAML module và bundle thành một contract dùng lúc chạy.** Tách paths, schemas, parameters và responses giúp nhóm sửa từng phần độc lập; Flask phục vụ bản bundle ở `/openapi.json` để Swagger UI và client dùng chung một đặc tả đã hợp nhất. Đổi lại, cần tạo lại `bundled-openapi.yaml` sau khi sửa các file nguồn.
2. **Tách HTTP/validation khỏi nghiệp vụ, đồng thời để server cấp ID.** Routes xử lý giao thức và validation, còn services quản lý dữ liệu; cách này giữ logic nghiệp vụ dễ kiểm thử và có thể thay lớp lưu trữ sau này. ID do server cấp để tránh client tạo ID trùng; lựa chọn lưu trữ hiện tại là in-memory nên dữ liệu sẽ mất khi khởi động lại.

## Cấu trúc thư mục

```text
SOA-Group-3/
├── README.md
├── task-api/
│   ├── README.md
│   ├── openapi.yaml
│   ├── bundled-openapi.yaml
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   └── services.py
│   ├── components/
│   │   ├── parameters.yaml
│   │   ├── request-bodies.yaml
│   │   ├── responses.yaml
│   │   └── schemas.yaml
│   ├── paths/
│   │   ├── authors.yaml
│   │   ├── books.yaml
│   │   └── borrows.yaml
│   └── tests/
│       ├── test_books.py
│       └── test_resources.py
└──
```

## Công nghệ sử dụng

- Python 3.x
- Flask
- OpenAPI 3.0 / YAML
- Redocly CLI (tạo bundle OpenAPI)
- Pytest
- JSON để trao đổi dữ liệu

## Danh sách endpoint

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/` | Trả về thông tin cơ bản của API. |
| GET | `/books` | Lấy danh sách tất cả sách. |
| GET | `/books/<book_id>` | Lấy thông tin sách theo ID. |
| POST | `/books` | Tạo mới một cuốn sách. |
| PUT | `/books/<book_id>` | Cập nhật thông tin sách theo ID. |
| DELETE | `/books/<book_id>` | Xóa sách theo ID. |
| GET | `/authors` | Lấy danh sách tất cả tác giả. |
| GET | `/authors/<author_id>` | Lấy thông tin tác giả theo ID. |
| POST | `/authors` | Tạo mới một tác giả. |
| PUT | `/authors/<author_id>` | Cập nhật thông tin tác giả theo ID. |
| DELETE | `/authors/<author_id>` | Xóa tác giả theo ID. |
| GET | `/borrows` | Lấy danh sách phiếu mượn. |
| GET | `/borrows/<borrow_id>` | Lấy thông tin phiếu mượn theo ID. |
| POST | `/borrows` | Tạo mới phiếu mượn. |
| PUT | `/borrows/<borrow_id>` | Cập nhật thông tin phiếu mượn. |
| DELETE | `/borrows/<borrow_id>` | Xóa phiếu mượn theo ID. |

## Quy ước chung của API

- Tất cả dữ liệu đầu vào và đầu ra đều sử dụng định dạng JSON.
- Mỗi resource có định danh duy nhất dạng số nguyên (`id`, `author_id`, `borrow_id`).
- Mã trạng thái HTTP phản ánh kết quả xử lý yêu cầu.
- Khi dữ liệu không hợp lệ, API trả về lỗi rõ ràng và mã trạng thái tương ứng.
- Tên trường dữ liệu được giữ thống nhất giữa request và response.
- Các endpoint đọc danh sách thường trả về cấu trúc dạng:

```json
{
  "data": [...],
  "total": 0
}
```

### Mã HTTP sử dụng

| Mã HTTP | Ý nghĩa |
|---|---|
| 200 OK | Yêu cầu thành công. |
| 201 Created | Tạo mới tài nguyên thành công. |
| 204 No Content | Xóa thành công, không có nội dung trả về. |
| 400 Bad Request | Dữ liệu đầu vào không hợp lệ hoặc thiếu trường bắt buộc. |
| 404 Not Found | Không tìm thấy tài nguyên tương ứng. |
| 415 Unsupported Media Type | Request không đúng định dạng JSON. |

## Hướng dẫn chạy dự án

### 1. Tạo môi trường ảo

```bash
python -m venv .venv
```

### 2. Kích hoạt môi trường ảo

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Cài đặt dependency

```bash
pip install -r requirements.txt
```

### 4. Chạy ứng dụng

```bash
python -m flask --app app run --debug
```

Mặc định, API sẽ chạy tại:

```text
http://127.0.0.1:5000
```

## Kiểm thử

```bash
pytest
```

Dự án hiện đang lưu dữ liệu bằng bộ nhớ trong quá trình chạy, nên khi khởi động lại server dữ liệu sẽ được reset về trạng thái ban đầu.

---

> Đây là dự án mẫu trong môn Kiến trúc hướng dịch vụ, tập trung vào việc mô tả API, xử lý resource, và triển khai API theo chuẩn REST với OpenAPI.

