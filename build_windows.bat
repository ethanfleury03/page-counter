@echo off
setlocal

set APP_NAME=PageCountRIP

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  set PYTHON=py -3
) else (
  set PYTHON=python
)

%PYTHON% -m pip install --upgrade pip pyinstaller
%PYTHON% -m pip install -r requirements.txt
%PYTHON% -m PyInstaller --clean --onefile --windowed --name %APP_NAME% page_count_rip.py

if not exist dist mkdir dist
copy /Y printer_config.example.json dist\printer_config.example.json >nul
copy /Y install_page_counter.bat dist\install_page_counter.bat >nul
copy /Y install_page_counter.ps1 dist\install_page_counter.ps1 >nul
copy /Y update_page_counter.bat dist\update_page_counter.bat >nul
copy /Y update_page_counter.ps1 dist\update_page_counter.ps1 >nul
copy /Y PageCountRIP-Setup.bat dist\PageCountRIP-Setup.bat >nul
copy /Y PRINT_COMPUTER_SETUP.md dist\PRINT_COMPUTER_SETUP.md >nul

echo.
echo Built executable should be at dist\%APP_NAME%.exe
pause
