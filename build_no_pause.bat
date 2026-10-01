@echo off
title Build AutoLoginTool
cd AutoLoginTool
"venv\Scripts\python.exe" -m pip install --upgrade pip
"venv\Scripts\python.exe" -m pip install pyinstaller
"venv\Scripts\pyinstaller.exe" --noconfirm --onefile --windowed --name AutoLoginTool --exclude-module matplotlib --exclude-module scipy --exclude-module tkinter --exclude-module IPython --exclude-module notebook --exclude-module pandas --exclude-module test --exclude-module pydoc --add-binary "C:\WINDOWS\system32\vcruntime140.dll;." --add-binary "C:\WINDOWS\system32\vcruntime140_1.dll;." --add-binary "C:\WINDOWS\system32\msvcp140.dll;." main.py
move /y "dist\AutoLoginTool.exe" "..\AutoLoginTool.exe"
rmdir /s /q build
rmdir /s /q dist
del /q AutoLoginTool.spec
cd ..
