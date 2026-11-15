# sumnote

**sumnote**는 문서를 업로드하면 AI가 핵심 내용을 요약하고, 사람이 확인할 검증 후보와 원문 근거를 제공하는 문서 검토 프로그램입니다. 문서 검토에 드는 시간을 줄이고 중요한 정보를 빠르게 찾는 것을 목표로 합니다.

## 현재 구현 상태

현재 실행 가능한 기능은 **문서 업로드와 파일 형식 확인**입니다.

- 지원 확장자: `.pdf`, `.txt`, `.docx`, `.xlsx`, `.xls`, `.csv`
- 파일 크기: 파일당 최대 10MB
- 형식 확인: 파일 내용이나 MIME 형식은 읽지 않고 파일명 확장자만 확인
- 처리 데이터: 업로드 파일을 분석하거나 저장하지 않음. DB 및 서버 파일로 보관하지 않음
- 프론트엔드와 백엔드: FastAPI 서버가 API와 정적 화면을 함께 제공

따라서 파일 이름이 `.pdf`여도 실제 PDF 내용인지 검사하지 않습니다. 현재 단계에서는 확장자와 크기만 확인하며, 텍스트 추출·AI 요약·검증·결과 화면·PDF/XLSX 생성은 아직 구현하지 않았습니다. PDF의 20페이지 제한과 스프레드시트의 표시 시트 제한도 추출 기능을 구현할 때 적용할 예정입니다.

## 전체 MVP 목표

문서 업로드 후 형식별 본문 또는 표 데이터를 공통 분석 입력으로 만들고, LLM AIagent API를 이용해 중요도 기반 계층형 요약과 검토 후보를 생성합니다. 원문 근거는 API 결과를 사용하며, AI는 사실관계를 최종 확정하지 않고 사람이 확인할 항목을 제공합니다.

전체 목표의 입력 및 출력은 다음과 같습니다.

| 입력 | 향후 처리 기준 | 결과 파일 |
| --- | --- | --- |
| PDF | 텍스트만 추출, 최대 20페이지, OCR 미지원 | PDF |
| TXT, DOCX | 파일 크기 최대 10MB, 페이지 제한 없음 | PDF |
| XLSX, XLS | 숨김 시트를 요약에서 제외하고 표시 시트 최대 10개 | PDF 및 XLSX |
| CSV | 하나의 시트로 취급 | PDF 및 XLSX |

전체 기능에는 결과 화면, 사용자 재시도 흐름도 포함됩니다. 문서와 결과는 DB나 임시 파일에 저장하지 않는 것을 목표로 합니다. 세부 구현 순서와 범위는 [`docs/MVP-plan.md`](../docs/MVP-plan.md), 상세 기능과 제한은 [`docs/requirements.md`](../docs/requirements.md) 및 [`docs/function-breakdown.md`](../docs/function-breakdown.md)를 참고하세요.

## 프로젝트 구조

```text
sumnote/
├── backend/
│   ├── app/
│   │   ├── api/          # 문서 API 및 입력·응답 스키마
│   │   ├── core/         # 공통 설정
│   │   ├── extractors/   # 형식별 추출기 자리
│   │   ├── services/     # 입력 확인 및 향후 처리 서비스
│   │   └── main.py       # FastAPI 앱, API 및 프론트엔드 제공
│   ├── tests/            # 백엔드 테스트 자리
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── .env.example
└── README.md
```

## 실행 방법

Python 3.9 이상을 설치한 뒤, `sumnote` 디렉토리에서 실행하세요.

### Windows PowerShell

```powershell
Set-Location .\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

### macOS 또는 Linux

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

화면: [http://127.0.0.1:8000](http://127.0.0.1:8000)  
API 문서: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## 업로드 확인 API

`POST /api/documents/validate?filename=report.txt`에 파일 바이트를 `application/octet-stream` 본문으로 전송합니다. 성공하면 파일명, 확장자, 확인한 크기와 지원 형식을 JSON으로 반환합니다.

- 지원하지 않는 확장자는 `415` 응답입니다.
- 10MB를 초과하면 `413` 응답입니다.
- 확장자는 대소문자를 구분하지 않습니다.
- 현재 API는 파일 내용을 분석하지 않으며, 업로드 데이터를 파일이나 DB에 저장하지 않습니다.

## 개발 범위 메모

MVP 설계서의 TXT 단일 형식은 남은 시간에 대한 권고안이며 확정 입력 범위는 아닙니다. 현재 업로드 확인은 요구사항에 명시된 6개 확장자를 허용합니다. 문서 추출과 AI 요약·검증은 후속 구현 범위입니다.
