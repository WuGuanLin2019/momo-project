@echo off
call conda activate funasr
cd /d "%~dp0"
python Funasr_server.py
pause