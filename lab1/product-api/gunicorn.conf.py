# Cấu hình Gunicorn WSGI Server (Slide 39)
bind = "0.0.0.0:5000"
workers = 2              # Điều chỉnh theo số lõi CPU
worker_class = "sync"
timeout = 60             # Worker timeout (giây)
graceful_timeout = 30    # Chờ xử lý xong các request dở dang trước khi tắt
keepalive = 5
preload_app = False
accesslog = "-"          # Ghi log truy cập ra stdout
errorlog = "-"           # Ghi log lỗi ra stderr
loglevel = "info"
proc_name = "product-api"
