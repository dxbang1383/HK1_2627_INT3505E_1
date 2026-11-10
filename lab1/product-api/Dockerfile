# ─── stage 1: builder ───
FROM python:3.12-slim AS builder
WORKDIR /build

COPY pyproject.toml requirements.txt ./
COPY src ./src

# Cài đặt uv để tạo venv và build gói dependencies siêu nhanh
RUN pip install --no-cache-dir uv \
    && uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH
RUN uv pip install --no-cache -r requirements.txt .

# ─── stage 2: runtime ───
FROM python:3.12-slim
WORKDIR /app

# Tạo non-root user 'app' vì lý do an toàn bảo mật (Slide 41)
RUN groupadd -r app && \
    useradd -r -g app -d /app app

# Copy virtual environment từ builder sang
COPY --from=builder --chown=app:app /opt/venv /opt/venv

# Copy mã nguồn và cấu hình máy chủ
COPY --chown=app:app src ./src
COPY --chown=app:app gunicorn.conf.py wsgi.py ./

ENV VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1

USER app
EXPOSE 5000

# Khởi chạy bằng Gunicorn WSGI Server (Slide 39)
CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]
