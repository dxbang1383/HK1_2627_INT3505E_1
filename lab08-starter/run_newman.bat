@echo off
echo [INFO] Running API tests with Newman...
newman.cmd run postman/books-api.postman_collection.json -e postman/local.postman_environment.json -r cli,junit --reporter-junit-export reports/junit.xml
if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] All test cases PASSED! Report saved to reports/junit.xml
) else (
    echo.
    echo [FAILED] Some tests failed. Please make sure Books API is running.
)
