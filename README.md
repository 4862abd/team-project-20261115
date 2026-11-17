# team-project-20261115

#1번 창: Backend
Set-Location .\sumnote\backend
python -m venv .venv --clear
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

#2번 창: Frontend
Set-Location .\sumnote\frontend
node .\server.mjs