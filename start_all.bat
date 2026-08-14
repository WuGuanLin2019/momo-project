@echo off

cd /d "%~dp0third_party\MeloTTS-main"
start "MOMO TTS" cmd /c "start_melo_server.bat"

cd /d "%~dp0third_party\Funasr"
start "MOMO funASR" cmd /c "start_server.bat"

cd /d "%~dp0"
start "MOMO" cmd /c "start.bat"

pause