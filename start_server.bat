@echo off
call conda activate melo
cd /d "%~dp0"
cd third_party/MeloTTS-main
python melo_server.py
pause