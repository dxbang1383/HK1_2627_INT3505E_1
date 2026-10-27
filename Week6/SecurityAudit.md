# Báo Cáo Rà Soát Bảo Mật (Security Audit) — Social Network API (Buổi 06)

Tài liệu này liệt kê **8 điểm có thể lộ thông tin / lỗ hổng bảo mật** (vượt mức yêu cầu tối thiểu $\ge 5$ điểm của bài tập) đối với 3 endpoint `POST /auth/login`, `POST /auth/refresh`, `GET /posts/{id}` và toàn bộ tầng Authentication / Authorization của API.

---

## Tóm tắt nhanh các điểm rà soát

| # | Điểm có thể lộ / Lỗ hổng | Endpoint ảnh hưởng | Phân loại OWASP / Slide B6 | Mức độ |
| :-: | :--- | :--- | :--- | :-: |
| **1** | Đọc trái phép bài viết riêng tư của người khác qua ID (**BOLA**) | `GET /posts/{id}` | OWASP API1:2023 | **Critical** |
| **2** | Dò tài khoản (User Enumeration), Timing Attack & Brute-force | `POST /auth/login` | OWASP API2:2023 | **High** |
| **3** | Lỗ hổng xác thực JWT (`alg=none`, Algorithm Confusion, dùng Access làm Refresh) | `POST /auth/refresh`, `GET /posts/{id}` | Slide 18 (Lỗi 01, 02, 07) | **Critical** |
| **4** | Lộ thông tin nhạy cảm (PII / `password_hash`) trong JWT Payload hoặc Response DTO | `POST /auth/login`, `GET /posts/{id}` | OWASP API3:2023 & Slide 18 (Lỗi 06) | **High** |
| **5** | Refresh Token bị đánh cắp nhưng không thể thu hồi hoặc dùng lại nhiều lần | `POST /auth/refresh` | Slide 15–18 (Lỗi 03, Revocation) | **High** |
| **6** | Lộ mật khẩu khi DB bị rò rỉ (dùng MD5/SHA-256 nhanh) hoặc lộ `JWT_SECRET_KEY` trên Git | Toàn hệ thống | Slide 3, 18 (Lỗi 04), 27–28 | **Critical** |
| **7** | Đánh cắp Token ở phía Client (`localStorage` XSS) hoặc lộ Token trong Server Log | Toàn hệ thống | Slide 9, 18 (Lỗi 05), 29 | **High** |
| **8** | Chỉ kiểm tra đăng nhập (AuthN) mà bỏ quên kiểm tra Scope / Role (AuthZ) | `GET /posts/{id}` & các route quản trị | OWASP API5:2023 & Slide 24–25 | **High** |

---