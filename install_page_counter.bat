@echo off
setlocal

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_page_counter.ps1" %*

