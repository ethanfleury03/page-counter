@echo off
setlocal

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0update_page_counter.ps1" %*

