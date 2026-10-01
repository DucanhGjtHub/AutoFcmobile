@echo off
title Build AutoLoginTool
echo ========================================================
echo DANG BUILD AUTOLOGINTOOL (CHE DO THU MUC - ON DINH HON)
echo ========================================================
echo.

cd AutoLoginTool

echo 0. Cap nhat pip...
"venv\Scripts\python.exe" -m pip install --upgrade pip

echo.
echo 1. Cai dat PyInstaller...
"venv\Scripts\python.exe" -m pip install pyinstaller

echo.
echo 2. Dong goi thanh THU MUC (onedir - chay duoc moi may)...
"venv\Scripts\pyinstaller.exe" --noconfirm --onedir --windowed --name AutoLoginTool --exclude-module matplotlib --exclude-module scipy --exclude-module tkinter --exclude-module IPython --exclude-module notebook --exclude-module pandas --exclude-module test --exclude-module pydoc main.py

echo.
echo 3. Copy thu muc ket qua ra ngoai...
if exist "..\AutoLoginTool_dist" rmdir /s /q "..\AutoLoginTool_dist"
xcopy /s /e /i /y "dist\AutoLoginTool" "..\AutoLoginTool_dist"

echo.
echo 4. Don dep build...
rmdir /s /q build
rmdir /s /q dist
del /q AutoLoginTool.spec
cd ..

echo.
echo ========================================================
echo HOAN TAT! Thu muc AutoLoginTool_dist da duoc tao!
echo Copy NGUYEN CA THU MUC do sang may kia, chay AutoLoginTool.exe ben trong.
echo ========================================================
pause

