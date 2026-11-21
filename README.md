# team-project-20261115
<br>

**실제 README 는 ./sumnote 에 있습니다.**
<br>
하단은 서버 실행법 입니다.<br>
<br>

#1번 창: Backend <br>
Set-Location .\sumnote\backend <br>
python -m venv .venv --clear <br>
.\.venv\Scripts\python.exe -m pip install -r requirements.txt <br>
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000 <br>

<br>

#2번 창: Frontend <br>
Set-Location .\sumnote\frontend <br>
node .\server.mjs<br>
