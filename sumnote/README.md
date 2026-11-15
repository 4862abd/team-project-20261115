# sumnote

현재 구현은 PDF, TXT, DOCX, XLSX, XLS, CSV 파일의 업로드와 확장자·크기 확인만 제공합니다. 파일 크기는 최대 10MB입니다. 파일 내용은 검사하지 않으며, 파일을 DB나 파일로 저장하지 않습니다.

## 실행 (Windows PowerShell)

```powershell
Set-Location .\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

브라우저에서 `http://127.0.0.1:8000`을 열면 업로드 화면이 표시됩니다.
