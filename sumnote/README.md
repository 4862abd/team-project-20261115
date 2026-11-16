# sumnote

**sumnote**는 문서를 올리면 AI가 중요도에 따라 요약하고, 사람이 확인할 검토 후보와 원문 근거를 보여 주는 문서 검토 프로그램입니다.

## 구성

- `frontend/`: 파일 선택·드래그 앤 드롭, 업로드 확인, 진행·오류 화면, 결과 대시보드
- `backend/`: 파일 제한 확인, 본문 추출, LLM AIagent 호출, PDF·XLSX 결과 생성
- Frontend와 Backend는 별도 서버 프로세스로 실행합니다. Frontend는 Node.js 기본 HTTP 서버만 사용하며 npm 패키지 설치가 필요하지 않습니다.

## 처리 기준

- 지원 입력: PDF, TXT, DOCX, XLSX, XLS, CSV
- 업로드 크기: 최대 10MB
- PDF: 텍스트 추출만 지원, 최대 20페이지, OCR 미지원
- XLSX·XLS: 숨김 시트 제외, 표시 시트 최대 10개
- CSV: 단일 시트로 처리
- 입력 결과: PDF, 스프레드시트 입력은 XLSX도 제공
- 원본과 결과는 DB 또는 임시 파일에 저장하지 않습니다.

형식 확인은 파일 확장자 기준입니다. PDF 페이지 수, Excel 시트 수, 파일 읽기 가능 여부는 요약 처리 단계에서 확인합니다.

## 환경 설정

Python 3.10 이상과 Node.js가 필요합니다. `sumnote/.env.example`에 실제 API 주소·키·모델을 설정합니다. Backend는 이 파일을 직접 읽습니다.

```powershell
Set-Location .\sumnote
notepad .env.example
```

`AIAGENT_API_URL`은 Chat Completions API 주소여야 합니다. OpenAI API 사용 예시는 `https://api.openai.com/v1/chat/completions`입니다. `AIAGENT_API_KEY`에는 실제 키, `AIAGENT_MODEL`에는 계정에서 사용할 수 있는 모델을 입력하세요. `.env.example`은 저장소에서 관리되는 파일이므로 실제 키를 입력한 변경 사항을 커밋하거나 공유하지 마세요.

## 실행 방법

PowerShell 창을 두 개 열고, 작업공간 루트(`team-project`)를 기준으로 실행합니다.

### 1번 창: Backend

```powershell
Set-Location .\sumnote\backend
python -m venv .venv --clear
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

### 2번 창: Frontend

```powershell
Set-Location .\sumnote\frontend
node .\server.mjs
```

이미 `sumnote` 폴더 안에 있다면 각 창에서 각각 `Set-Location .\backend`, `Set-Location .\frontend`로 이동합니다. `sumnote` 안에서 `Set-Location .\sumnote\backend`를 실행하면 잘못된 중첩 경로가 됩니다.

- 앱: [http://127.0.0.1:5173](http://127.0.0.1:5173)
- Backend API 문서: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Backend 상태 확인: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

## 화면 흐름

1. 파일을 찾아 선택하거나 업로드 영역에 끌어 놓습니다.
2. `업로드 및 형식 확인`을 누르면 Backend가 확장자와 크기를 확인하고 파일 정보를 표시합니다.
3. 확인이 완료되면 `문서 요약 시작` 버튼이 활성화됩니다.
4. 진행 화면에서 처리 상태를 보고, 오류가 발생하면 원인과 재시도·첫 화면 이동 버튼을 확인합니다.
5. 결과 대시보드에서 요약·원문 근거·검토 항목 탭을 전환하고 페이지 버튼으로 읽습니다. 결과 영역은 내부 스크롤 없이 페이지 단위로 표시합니다.

## API 경로

| 메서드·경로 | 설명 |
| --- | --- |
| `GET /api/health` | Backend 상태 확인 |
| `POST /api/documents/validate?filename=...` | 확장자와 업로드 크기 확인 |
| `POST /api/documents/process?filename=...` | 본문 추출, 요약·검증 결과 반환 |
| `POST /api/documents/download/pdf` | PDF 결과 생성 및 다운로드 |
| `POST /api/documents/download/xlsx` | 스프레드시트 XLSX 결과 생성 및 다운로드 |

Frontend는 기본적으로 `http://127.0.0.1:8000/api`를 Backend 주소로 사용합니다. Backend 주소를 바꾸려면 `frontend/app.js`의 `SUMNOTE_API_BASE_URL` 기본값을 변경하세요.

자세한 요구사항은 [`../docs/requirements.md`](../docs/requirements.md), MVP 범위와 구현 순서는 [`../docs/MVP-plan.md`](../docs/MVP-plan.md)를 참고하세요.
