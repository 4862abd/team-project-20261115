# sumnote API 명세서

## 1. 문서 정보

| 항목 | 내용 |
| --- | --- |
| API 이름 | sumnote Backend API |
| 버전 | 0.2.0 |
| 기준 | 현재 `sumnote/backend` 구현 |
| 기본 주소(로컬) | `http://127.0.0.1:8000` |
| OpenAPI UI | `/docs` |

이 문서는 구현된 API 동작을 기술한다. API는 인증을 요구하지 않으며, 원본 문서 및 처리 결과를 DB나 임시 파일에 저장하지 않는다. 업로드 데이터는 요청 본문으로 전달하고 메모리에서 처리한다.

## 2. 공통 규칙

- API 경로 접두사는 `/api`이다.
- 요청 본문은 UTF-8 JSON 또는 문서의 원시 바이트이며, 각 경로의 Content-Type을 따른다.
- 오류 JSON은 `{ "error": { "code": "오류 코드", "message": "오류 설명" } }` 형식이다.
- 모든 응답에는 `Cache-Control: no-store`가 설정된다. 파일 다운로드 응답에는 UTF-8 파일명을 지정하는 `Content-Disposition` 헤더도 포함된다.
- 브라우저 CORS 허용 Origin은 `http://127.0.0.1:5173`, `http://localhost:5173`이며 허용 메서드는 GET, POST, OPTIONS이다.
- 지원 확장자는 `.pdf`, `.txt`, `.docx`, `.xlsx`, `.xls`, `.csv`이며 대소문자를 구분하지 않는다. 최대 업로드 크기는 10 MiB(10,485,760 bytes)이다.
- 업로드 파일명은 쿼리 파라미터로 전달한다. 파일 형식은 MIME 타입이나 파일 시그니처가 아니라 파일명 확장자로 판정한다.

## 3. 엔드포인트 요약

| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| `GET` | `/api/health` | Backend 상태 확인 |
| `POST` | `/api/documents/validate?filename={filename}` | 파일 크기와 확장자 확인 |
| `POST` | `/api/documents/process?filename={filename}` | 문서 추출, 요약 및 검증 |
| `POST` | `/api/documents/download/pdf` | 처리 결과 PDF 생성 및 다운로드 |
| `POST` | `/api/documents/download/xlsx` | 스프레드시트 처리 결과 XLSX 생성 및 다운로드 |

## 4. 엔드포인트 상세

### 4.1 상태 확인

`GET /api/health`

Backend 프로세스가 요청을 처리할 수 있는지 확인한다.

**성공 응답 — `200 OK`**

```json
{
  "status": "ok"
}
```

### 4.2 파일 업로드 확인

`POST /api/documents/validate?filename={filename}`

원시 파일 바이트를 스트리밍으로 전송한다. 확장자와 업로드 크기를 확인하고, 파일 내용은 파싱하지 않는다. 확인 후 업로드 바이트는 메모리에서 정리한다.

**요청**

| 항목 | 값 |
| --- | --- |
| Query | `filename` (필수): 원본 파일명. URL 인코딩 필요 |
| Header | `Content-Type: application/octet-stream` 권장 |
| Body | 파일의 원시 바이트 |

**성공 응답 — `200 OK`**

```json
{
  "filename": "회의록.pdf",
  "extension": ".pdf",
  "format": "PDF 문서",
  "size_bytes": 24576,
  "max_size_bytes": 10485760,
  "format_check": "extension_only",
  "stored": false,
  "message": "지원 확장자에 해당하는 파일입니다. 파일 내용은 검사하거나 저장하지 않았습니다."
}
```

`format_check`은 확장자만 확인했음을 뜻한다. 성공 응답은 파일이 실제로 해당 형식인지, 파일 내용이 읽을 수 있는지 보증하지 않는다.

**오류 응답**

| HTTP 상태 | 코드 | 설명 |
| --- | --- | --- |
| `400` | `FILENAME_REQUIRED` | 파일명이 없거나 공백임 |
| `400` | `INVALID_CONTENT_LENGTH` | `Content-Length`가 정수가 아님 |
| `413` | `FILE_TOO_LARGE` | 10 MiB 초과 |
| `415` | `UNSUPPORTED_FORMAT` | 지원하지 않는 확장자 |

### 4.3 문서 처리

`POST /api/documents/process?filename={filename}`

원시 파일 바이트를 전달한다. 파일 형식별 텍스트/표를 추출하고 AI 분석 API를 호출해 요약과 검토 후보를 반환한다. PDF는 텍스트만 추출하며 OCR을 수행하지 않는다. 스프레드시트는 숨김 시트를 제외하고 최대 10개 표시 시트를 처리한다.

**요청**

| 항목 | 값 |
| --- | --- |
| Query | `filename` (필수): 원본 파일명. URL 인코딩 필요 |
| Header | `Content-Type: application/octet-stream` 권장 |
| Body | 파일의 원시 바이트 |

**성공 응답 — `200 OK`**

정상 분석, 검토 필요, 처리 실패 및 분석 결과 없음은 `ProcessingResult` 형태로 응답한다. 처리 실패도 일반적으로 HTTP `200`이며, 성공 여부는 `status`로 판단한다.

```json
{
  "document": {
    "filename": "회의록.pdf",
    "extension": ".pdf",
    "format": "PDF 문서",
    "size_bytes": 24576,
    "page_count": 3,
    "sheet_count": null,
    "sheets": []
  },
  "status": "completed",
  "status_message": "요약과 검토 결과가 준비되었습니다.",
  "summary": {
    "title": "회의록",
    "one_line_summary": "분기 계획과 담당 일정을 논의했다.",
    "overview": "회의의 주요 안건과 결정 사항을 정리했다.",
    "topics": ["분기 계획"],
    "keywords": ["일정", "담당자"],
    "key_points": [
      {
        "level": "대단락",
        "importance": "높음",
        "title": "일정 확정",
        "content": "시범 운영을 12월에 시작한다.",
        "evidence": [{ "quote": "시범 운영은 12월부터 시작한다.", "location": "2페이지" }]
      }
    ],
    "important_facts": [
      {
        "label": "시작 시점",
        "value": "12월",
        "importance": "높음",
        "evidence": [{ "quote": "시범 운영은 12월부터 시작한다.", "location": "2페이지" }]
      }
    ],
    "sheet_summaries": [],
    "conclusion": ""
  },
  "verification": {
    "generated": true,
    "status": "검토 완료",
    "items": []
  }
}
```

#### 응답 필드

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `document` | `DocumentInfo` | 문서 정보 및 스프레드시트 시트 메타데이터 |
| `document.filename` | string | 경로를 제외한 원본 파일명 |
| `document.extension` | string | 소문자 확장자. 식별되지 않으면 오류 결과에서 `없음`일 수 있음 |
| `document.format` | string | 형식 표시명 |
| `document.size_bytes` | integer | 업로드 크기(bytes) |
| `document.page_count` | integer 또는 null | PDF 페이지 수. PDF 외에는 보통 null |
| `document.sheet_count` | integer 또는 null | 스프레드시트의 표시 시트 수. 해당 없으면 null |
| `document.sheets` | `SheetInfo[]` | 시트명, 헤더, 데이터 행 수. 비 스프레드시트는 빈 배열 |
| `status` | enum | `completed`, `needs_review`, `failed`, `no_result` |
| `status_message` | string | 사람이 읽을 수 있는 처리 상태 설명 |
| `summary` | `SummaryData` | 요약 결과. 결과가 없거나 실패해도 기본값 객체가 반환될 수 있음 |
| `verification` | `VerificationData` | 검증 생성 여부, 상태, 검토 후보 목록 |

#### 하위 객체

`SheetInfo`는 `{ "name": string, "headers": string[], "data_row_count": integer }`이다.

`SummaryData` 필드는 다음과 같다.

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `title` | string | 문서 제목 |
| `one_line_summary` | string | 한 줄 요약 |
| `overview` | string | 전체 개요 |
| `topics` | string[] | 주요 주제 |
| `keywords` | string[] | 키워드 |
| `key_points` | `KeyPoint[]` | 중요도와 계층을 포함한 핵심 내용 |
| `important_facts` | `ImportantFact[]` | 주요 인물·기관·날짜·수치·조건 |
| `sheet_summaries` | `SheetSummary[]` | 시트별 요약 |
| `conclusion` | string | 원문에 있는 결론. 없으면 빈 문자열 |

- `KeyPoint`: `{ "level": string, "importance": string, "title": string, "content": string, "evidence": Evidence[] }`
- `ImportantFact`: `{ "label": string, "value": string, "importance": string, "evidence": Evidence[] }`
- `SheetSummary`: `{ "sheet_name": string, "content": string, "evidence": Evidence[] }`
- `Evidence`: `{ "quote": string, "location": string }`. 근거나 위치가 없으면 빈 인용 또는 `없음`으로 표현될 수 있다.
- 중요도 값은 `높음`, `중간`, `낮음`; 핵심 내용 단계는 `대단락`, `중단락`, `소단락`이다.

`VerificationData`는 `{ "generated": boolean, "status": string, "items": VerificationItem[] }`이다. 각 `VerificationItem`은 `category`, `importance`, `issue`, `reason`, `status`, `evidence` 필드를 가진다. 검증 항목은 외부 사실 판정이 아니라 원문에서 사람이 확인할 후보이다.

#### 상태 판정

| 값 | 의미 |
| --- | --- |
| `completed` | 요약이 있고 검증이 생성되었으며 확인이 필요한 항목이나 핵심 근거 누락이 없음 |
| `needs_review` | 검증 미생성, 검토 후보 존재 또는 핵심 내용의 원문 근거 누락 |
| `failed` | 파일 확인·추출·AI 처리 중 오류 |
| `no_result` | 분석 가능한 텍스트가 없거나 요약 결과를 만들지 못함 |

`failed` 및 `no_result` 응답에서는 `summary`와 `verification`이 기본값으로 채워질 수 있다. 클라이언트는 HTTP 상태만으로 처리 성공 여부를 판단하지 말고 `status`를 확인해야 한다.

**처리 오류 응답 예시 (`200 OK`, `status: failed`)**

```json
{
  "document": {
    "filename": "회의록.pdf",
    "extension": ".pdf",
    "format": "PDF 문서",
    "size_bytes": 24576,
    "page_count": null,
    "sheet_count": null,
    "sheets": []
  },
  "status": "failed",
  "status_message": "문서 처리 중 오류가 발생했습니다. 다시 시도해 주세요.",
  "summary": {
    "title": "회의록",
    "one_line_summary": "",
    "overview": "",
    "topics": [],
    "keywords": [],
    "key_points": [],
    "important_facts": [],
    "sheet_summaries": [],
    "conclusion": ""
  },
  "verification": { "generated": false, "status": "생성되지 않음", "items": [] }
}
```

처리 단계에서 발생하는 오류 코드에는 `FILENAME_REQUIRED`, `INVALID_CONTENT_LENGTH`, `FILE_TOO_LARGE`, `UNSUPPORTED_FORMAT`, `EMPTY_DOCUMENT`, `PDF_TEXT_NOT_FOUND`, `SHEET_LIMIT_EXCEEDED`, `AIAGENT_NOT_CONFIGURED`, `AIAGENT_TIMEOUT`, `AIAGENT_REQUEST_FAILED`, `AIAGENT_RESPONSE_NOT_JSON`, `AIAGENT_RESPONSE_INVALID`, `AI_ANALYSIS_FAILED`, `PROCESSING_FAILED` 등이 있다. 이 경로에서는 이 오류들이 위 `failed` 또는 `no_result` 결과에 `status_message`로 전달되며 오류 코드 자체는 결과 스키마에 포함되지 않는다.

### 4.4 PDF 결과 다운로드

`POST /api/documents/download/pdf`

요청에 포함된 `ProcessingResult`를 PDF로 변환해 다운로드 응답으로 반환한다. 모든 입력 형식에 사용할 수 있으며, 성공·검토 필요·실패·결과 없음 상태의 결과 객체를 받을 수 있다.

**요청**

`Content-Type: application/json`이며 본문은 4.3의 `ProcessingResult` 전체 객체이다.

**성공 응답 — `200 OK`**

| 헤더 | 값 |
| --- | --- |
| `Content-Type` | `application/pdf` |
| `Content-Disposition` | `attachment; filename*=UTF-8''{URL 인코딩 파일명}` |
| 파일명 | `{원본 파일명(확장자 제외)}_summary.pdf` |

예: `회의록.pdf` → `회의록_summary.pdf`

**오류 응답**

| HTTP 상태 | 코드 | 설명 |
| --- | --- | --- |
| `500` | `PDF_GENERATION_FAILED` | 결과 PDF 생성 실패 |

오류는 공통 오류 JSON으로 반환된다.

### 4.5 XLSX 결과 다운로드

`POST /api/documents/download/xlsx`

요청에 포함된 `ProcessingResult`를 XLSX 파일로 변환한다. 입력 문서의 `document.extension`이 `.xlsx`, `.xls`, `.csv`인 경우에만 사용할 수 있다.

**요청**

`Content-Type: application/json`이며 본문은 4.3의 `ProcessingResult` 전체 객체이다.

**성공 응답 — `200 OK`**

| 헤더 | 값 |
| --- | --- |
| `Content-Type` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `Content-Disposition` | `attachment; filename*=UTF-8''{URL 인코딩 파일명}` |
| 파일명 | `{원본 파일명(확장자 제외)}_summary.xlsx` |

**오류 응답**

| HTTP 상태 | 코드 | 설명 |
| --- | --- | --- |
| `400` | `XLSX_NOT_AVAILABLE` | 스프레드시트 입력이 아님 |
| `500` | `XLSX_GENERATION_FAILED` | 결과 XLSX 생성 실패 |

## 5. 공통 오류 형식과 코드

HTTP 오류 응답은 다음 JSON 구조이다.

```json
{
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "파일 크기가 10MB를 초과했습니다. 10MB 이하 파일을 선택해 주세요."
  }
}
```

`validate` 및 다운로드 API는 아래와 같이 해당 오류의 HTTP 상태 코드를 반환한다. `process`는 처리 중 발생한 예외를 결과 객체의 `status`와 `status_message`로 바꾸어 HTTP `200`으로 반환한다.

| 코드 예시 | HTTP 상태(직접 오류 응답일 때) |
| --- | ---: |
| `FILENAME_REQUIRED`, `INVALID_CONTENT_LENGTH` | 400 |
| `XLSX_NOT_AVAILABLE` | 400 |
| `FILE_TOO_LARGE` | 413 |
| `UNSUPPORTED_FORMAT` | 415 |
| `AIAGENT_NOT_CONFIGURED` | 503 |
| `AIAGENT_TIMEOUT` | 504 |
| AI Agent 응답/요청 실패 | 502 |
| PDF/XLSX 결과 생성 실패 | 500 |

## 6. 사용 예시

### 업로드 확인 및 처리

```bash
curl -X POST "http://127.0.0.1:8000/api/documents/validate?filename=meeting.pdf" \
  -H "Content-Type: application/octet-stream" \
  --data-binary "@meeting.pdf"

curl -X POST "http://127.0.0.1:8000/api/documents/process?filename=meeting.pdf" \
  -H "Content-Type: application/octet-stream" \
  --data-binary "@meeting.pdf"
```

처리 응답 JSON을 그대로 `/api/documents/download/pdf`에 POST하면 결과 PDF를 받을 수 있다. 스프레드시트 입력이면 같은 결과 객체를 `/api/documents/download/xlsx`로 전달한다.

## 7. 관련 문서

- 실행 및 화면 흐름: [`sumnote/README.md`](../sumnote/README.md)
- 제품 요구사항: [`requirements.md`](requirements.md)
- MVP 범위: [`MVP-plan.md`](MVP-plan.md)
