@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist .venv (
  python -m venv .venv
  call .venv\Scripts\activate.bat
  pip install -r requirements.txt
) else (
  call .venv\Scripts\activate.bat
)
set LLM_PROVIDER=openai
set LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
set LLM_MODEL=gemini-flash-latest
if not exist key.txt (
  set /p KEY=Вставьте ключ Gemini API и нажмите Enter: 
  echo %KEY%> key.txt
)
set /p LLM_API_KEY=<key.txt
start http://localhost:5000
python -m web.app
