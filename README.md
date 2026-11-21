# team-project-20261115
/n

**실제 README 는 ./sumnote 에 있습니다.**
/n
하단은 서버 실행법 입니다./n
/n

#1번 창: Backend /n
Set-Location .\sumnote\backend /n
python -m venv .venv --clear /n
.\.venv\Scripts\python.exe -m pip install -r requirements.txt /n
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000 /n

/n

#2번 창: Frontend /n
Set-Location .\sumnote\frontend /n
node .\server.mjs/n
