# Lab 4 — Phân tích kết quả thực nghiệm

| Kịch bản | Users | Spawn rate | Duration | p95 (ms) | Failure rate | RPS |
|---|---:|---:|---:|---:|---:|---:|
| **A** | 10 | 2 | 30s | 28 ms | 0.00% | 4.76 req/s |
| **B** | 50 | 5 | 60s | 30 ms | 0.51% | 23.21 req/s |
| **C** | 200 | 50 | 30s | 110 ms | 0.42% | 96.65 req/s |

---

### 1. Kịch bản có p95 cao nhất là gì? Dùng số liệu quan sát để giải thích.
* **Kịch bản C (200 users)** có $p95$ cao nhất (**110 ms**), cao gấp gần 4 lần kịch bản B (30 ms) và A (28 ms).
* **Giải thích:** Khi số lượng người dùng đồng thời tăng vọt lên 200 (tốc độ spawn 50 user/giây), máy chủ Flask development server (chạy đơn tiến trình) và cơ chế khóa file của SQLite bị dồn ứ hàng đợi request (request queue contention). Mặc dù trung vị $p50$ vẫn duy trì ở mức 14 ms, nhưng 5% các request chậm nhất bị dồn tích lũy dẫn đến $p95$ tăng vọt lên 110 ms và đuôi độ trễ $p99$ đạt 170 ms (thời gian phản hồi lớn nhất đạt 340 ms).

---

### 2. Endpoint nào tăng failure rate? Phân biệt lỗi HTTP thực và lỗi đánh dấu trong Locust.
* **Endpoint ghi nhận lỗi:** Chỉ có `GET /books?year=` có failure rate (A: 0%, B: 0.51% với 7 lỗi, C: 0.42% với 12 lỗi).
* **Phân biệt:** 
  * Đây **không phải lỗi HTTP thực tế (5xx)** từ server. Phía server Flask thực tế vẫn trả về HTTP 200 OK bình thường.
  * Đây là **lỗi đánh dấu có chủ đích ở client (Locust)** thông qua đoạn mã `if random.random() < 0.01: response.failure(...)` trong `locustfile.py` để mô phỏng tỷ lệ lỗi nhân tạo 1%.

---

### 3. Với SLO giả định p95 < 300 ms, kịch bản nào đạt? Nêu giới hạn của phép đo.
* **Đánh giá SLO:** Cả 3 kịch bản A, B, C đều **đạt** yêu cầu $p95 < 300\text{ ms}$ (lần lượt là $28\text{ ms}, 30\text{ ms}, 110\text{ ms} < 300\text{ ms}$).
* **Đề xuất baseline cho CI gate:** Với mức tải thông thường 50 users (Kịch bản B), đề xuất ngưỡng CI gate là **$p95 \le 100\text{ ms}$** và **tỷ lệ lỗi $\le 1\%$**. Nếu $p95 > 100\text{ ms}$, hệ thống CI sẽ chặn bản build để ngăn ngừa suy giảm hiệu năng (performance regression).
* **Giới hạn phép đo:** Thử nghiệm chạy trên máy cá nhân (localhost) sử dụng SQLite và Flask development server. Môi trường này chưa có độ trễ mạng thực tế (network latency), chưa có TLS overhead và cơ chế connection pooling thực tế của các RDBMS production như PostgreSQL.

---

### 4. Nếu connection pool bị giới hạn ở 5, bạn sẽ kiểm chứng ảnh hưởng như thế nào?
* **Hiện tượng xảy ra:** Khi 200 users đồng thời gửi request, hệ thống chỉ có tối đa 5 kết nối mở tới CSDL. Các request vượt quá số lượng này sẽ phải xếp hàng chờ trong `pool_timeout`. Khi hàng đợi đầy hoặc hết thời gian chờ (timeout), SQLAlchemy sẽ ném ra lỗi `TimeoutError: QueuePool limit of size 5 reached`, dẫn tới hàng loạt request bị trả về lỗi HTTP 500 hoặc rớt kết nối.
* **Cách kiểm chứng bằng Locust:**
  1. Cấu hình giới hạn pool trong Flask:
     ```python
     SQLALCHEMY_ENGINE_OPTIONS = {
         "pool_size": 5,
         "max_overflow": 0,
         "pool_timeout": 2  # timeout ngắn 2 giây để kích hoạt lỗi nhanh
     }
     ```
  2. Chạy kịch bản C (`locust -u 200 -r 50 -t 30s`).
  3. Quan sát trên bảng thống kê của Locust: Cột `# fails` sẽ tăng đột biến (Failure rate $> 10-30\%$) với các lỗi `HTTPError: 500 Internal Server Error` do cạn kiệt connection pool.
