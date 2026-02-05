@echo off
echo ========================================
echo   POLYMARKET WEB - DEPLOY TO VPS
echo ========================================
echo.

echo [1/3] Creating deploy package...
if exist deploy rmdir /s /q deploy
mkdir deploy
copy web_app.py deploy\ >nul
copy bot.py deploy\ >nul
copy requirements.txt deploy\ >nul
copy Dockerfile deploy\ >nul
copy docker-compose.yml deploy\ >nul
copy .env deploy\ >nul
xcopy /E /I templates deploy\templates >nul
echo Done!

echo.
echo [2/3] Uploading to VPS (141.227.165.46)...
scp -r deploy ubuntu@141.227.165.46:~/polymarket-web
echo Done!

echo.
echo [3/3] Starting Docker container on VPS...
ssh ubuntu@141.227.165.46 "cd polymarket-web && docker stop polymarket-web 2>/dev/null; docker rm polymarket-web 2>/dev/null; docker build -t polymarket-web . && docker run -d -p 5000:5000 --name polymarket-web --restart unless-stopped polymarket-web"
echo Done!

echo.
echo ========================================
echo   DEPLOYMENT COMPLETE!
echo ========================================
echo.
echo Access at: http://141.227.165.46:5000
echo.
pause
