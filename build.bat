@echo off
echo ============================================
echo   Building FTP-Client in .exe (ONEDIR)
echo ============================================
echo.

REM Check PyInstaller
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [!] PyInstaller not found. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo [X] Failed to install PyInstaller
        pause
        exit /b 1
    )
)

echo [1/2] Clearing previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist FTPClient.spec del /q FTPClient.spec

echo [2/2] Building...
python -m PyInstaller ^
    --onedir ^
    --noconsole ^
    --name FTPClient ^
    --add-data "icons;icons" ^
    --icon "icon.ico" ^
    --hidden-import ftplib ^
    --hidden-import PyQt5.QtCore ^
    --hidden-import PyQt5.QtGui ^
    --hidden-import PyQt5.QtWidgets ^
    --hidden-import screeninfo ^
    main.py

if errorlevel 1 (
    echo.
    echo [X] Build failed
    pause
    exit /b 1
)

echo.
echo ============================================
echo   DONE!
echo   .exe is in: dist\FTPClient.exe
echo ============================================
pause