@echo off
setlocal enabledelayedexpansion
title Cai Dat Nhanh AutoFcmobile (Khong can Git / Python)
echo ===================================================
echo     TOOL CAI DAT TU DONG AUTOFCMOBILE SOURCE CODE
echo ===================================================
echo.

:: 1. Kiem tra Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [!] May chua co Python. Dang tai Python 3.10...
    curl -L -o python_installer.exe https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe
    echo [!] Dang cai dat Python an (Vui long doi khoang 1-2 phut)...
    start /wait python_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_test=0
    echo [OK] Da cai dat xong Python!
    set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python310\python.exe"
    del python_installer.exe
) ELSE (
    echo [OK] Python da duoc cai dat tren may nay.
    set "PYTHON_EXE=python"
)

:: 2. Tai source code Github
echo.
echo [!] Dang tai ma nguon moi nhat tu Github...
if exist master.zip del master.zip
curl -L -o master.zip https://github.com/DucanhGjtHub/AutoFcmobile/archive/refs/heads/master.zip

:: 3. Giai nen
echo [!] Dang giai nen ma nguon...
powershell -command "Expand-Archive -Force master.zip ."
if exist AutoFcmobile_Dev rmdir /s /q AutoFcmobile_Dev
ren AutoFcmobile-master AutoFcmobile_Dev
del master.zip

:: 4. Cai thu vien
echo.
echo [!] Dang thiet lap moi truong venv va cai thu vien...
cd AutoFcmobile_Dev\AutoLoginTool
"!PYTHON_EXE!" -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
echo [!] Dang tai cac thu vien (PyQt5, OpenCV, v.v...)...
pip install -r requirements.txt

:: 5. Tao file khoi dong
echo @echo off > Chay_Tool.bat
echo title AutoFcmobile >> Chay_Tool.bat
echo call venv\Scripts\activate.bat >> Chay_Tool.bat
echo python main.py >> Chay_Tool.bat
echo pause >> Chay_Tool.bat

echo.
echo ===================================================
echo [OK] CAI DAT HOAN TAT THANG CONG 100%%!
echo Ma nguon duoc luu tai thu muc: AutoFcmobile_Dev
echo Da tao san file khoi dong Chay_Tool.bat cho ban.
echo ===================================================
echo Nhan phim bat ky de thoat...
pause >nul
