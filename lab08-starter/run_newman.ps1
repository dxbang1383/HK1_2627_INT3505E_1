# Script chạy kiểm thử tự động toàn bộ Collection bằng Newman CLI (Slide 22)
# Yêu cầu: Server Books API (python -m app --port 5000) đang chạy

Write-Host ">>> Đang chạy kiểm thử API với Newman..." -ForegroundColor Cyan

newman.cmd run postman/books-api.postman_collection.json `
    -e postman/local.postman_environment.json `
    -r cli,junit `
    --reporter-junit-export reports/junit.xml

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n>>> [THÀNH CÔNG] Toàn bộ 7 test cases đã PASS 100%! Báo cáo đã lưu tại reports/junit.xml" -ForegroundColor Green
} else {
    Write-Host "`n>>> [THẤT BẠI] Có test case bị lỗi. Vui lòng kiểm tra lại server Books API." -ForegroundColor Red
}
