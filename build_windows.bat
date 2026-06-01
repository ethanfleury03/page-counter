@echo off
setlocal

python -m pip install --upgrade pyinstaller
python -m pip install -r requirements.txt
python -m PyInstaller --onefile --windowed --name PageCountRIP page_count_rip.py

echo.
echo Built executable should be at dist\PageCountRIP.exe
pause
