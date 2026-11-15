import asyncio
from pathlib import PurePosixPath
from urllib.parse import quote

from fastapi import APIRouter, Query, Request
from fastapi.responses import Response

from app.api.schemas.document import DocumentInfo, DocumentUploadResult, SheetInfo
from app.api.schemas.result import ProcessingResult, SummaryData, VerificationData
from app.core.config import FORMAT_LABELS, MAX_UPLOAD_SIZE_BYTES, SUPPORTED_EXTENSIONS
from app.extractors.docx import extract_docx
from app.extractors.pdf import extract_pdf
from app.extractors.spreadsheet import extract_csv, extract_xls, extract_xlsx
from app.extractors.txt import extract_txt
from app.services.errors import ProcessingError
from app.services.file_validation import validate_filename, validate_upload_size
from app.services.pdf_report import build_pdf_report
from app.services.processing_session import ProcessingSession
from app.services.summarization import SummarizationService
from app.services.xlsx_report import build_xlsx_report


router = APIRouter()
summarization_service = SummarizationService()
SPREADSHEET_EXTENSIONS = {".xlsx", ".xls", ".csv"}


async def _read_into_session(request: Request, session: ProcessingSession) -> int:
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            declared_size = int(content_length)
        except ValueError as error:
            raise ProcessingError("INVALID_CONTENT_LENGTH", "업로드 크기를 확인할 수 없습니다.", 400) from error
        validate_upload_size(declared_size)

    async for chunk in request.stream():
        session.append(chunk)
        validate_upload_size(session.size)
    return session.size


def _initial_document(filename: str, size_bytes: int = 0) -> DocumentInfo:
    normalized = filename.replace("\\", "/")
    extension = PurePosixPath(normalized).suffix.lower()
    return DocumentInfo(
        filename=PurePosixPath(normalized).name or "없음",
        extension=extension or "없음",
        format=FORMAT_LABELS.get(extension, "지원하지 않는 형식"),
        size_bytes=size_bytes,
    )


def _failure_result(filename: str, size_bytes: int, error: ProcessingError) -> ProcessingResult:
    document = _initial_document(filename, size_bytes)
    stem = PurePosixPath(filename.replace("\\", "/")).stem or filename
    status = "no_result" if error.code in {"PDF_TEXT_NOT_FOUND", "EMPTY_DOCUMENT"} else "failed"
    return ProcessingResult(
        document=document,
        status=status,
        status_message=error.message,
        summary=SummaryData(title=stem),
        verification=VerificationData(generated=False, status="생성되지 않음"),
    )


def _extract(extension: str, data: bytes, filename: str):
    if extension == ".txt":
        return extract_txt(data)
    if extension == ".pdf":
        return extract_pdf(data)
    if extension == ".docx":
        return extract_docx(data)
    if extension == ".xlsx":
        return extract_xlsx(data)
    if extension == ".xls":
        return extract_xls(data)
    if extension == ".csv":
        return extract_csv(data, filename)
    raise ProcessingError("UNSUPPORTED_FORMAT", "지원하지 않는 파일 형식입니다.", 415)


async def _summarize_until_complete_or_cancelled(request: Request, **kwargs):
    task = asyncio.create_task(summarization_service.summarize_and_verify(**kwargs))
    try:
        while True:
            done, _ = await asyncio.wait({task}, timeout=0.25)
            if task in done:
                return task.result()
            if await request.is_disconnected():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
                raise ProcessingError(
                    "PROCESSING_CANCELLED",
                    "사용자가 처리를 취소했습니다. 입력 자료를 정리했습니다.",
                    499,
                )
    except BaseException:
        if not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        raise


@router.post("/documents/validate", response_model=DocumentUploadResult)
async def upload_and_check_format(
    request: Request,
    filename: str = Query(default=""),
) -> DocumentUploadResult:
    session = ProcessingSession()
    try:
        size_bytes = await _read_into_session(request, session)
        extension, format_label = validate_filename(filename)
        return DocumentUploadResult(
            filename=filename,
            extension=extension,
            format=format_label,
            size_bytes=size_bytes,
            max_size_bytes=MAX_UPLOAD_SIZE_BYTES,
            format_check="extension_only",
            stored=False,
            message="지원 확장자에 해당하는 파일입니다. 파일 내용은 검사하거나 저장하지 않았습니다.",
        )
    finally:
        session.clear()


@router.post("/documents/process", response_model=ProcessingResult)
async def process_document(
    request: Request,
    filename: str = Query(default=""),
) -> ProcessingResult:
    session = ProcessingSession()
    size_bytes = 0
    content = b""
    extracted = None
    try:
        size_bytes = await _read_into_session(request, session)
        extension, format_label = validate_filename(filename)
        content = session.content()
        extracted = _extract(extension, content, filename)
        if not extracted.text.strip():
            raise ProcessingError(
                "EMPTY_DOCUMENT",
                "문서에서 분석할 텍스트를 찾지 못했습니다. 파일 내용을 확인해 주세요.",
                422,
            )

        sheets = [
            SheetInfo(name=sheet.name, headers=sheet.headers, data_row_count=sheet.data_row_count)
            for sheet in extracted.sheets
        ]
        result = await _summarize_until_complete_or_cancelled(
            request,
            text=extracted.text,
            filename=PurePosixPath(filename.replace("\\", "/")).name,
            extension=extension,
            format_label=format_label,
            size_bytes=size_bytes,
            page_count=extracted.page_count,
            sheet_count=len(sheets) if extension in SPREADSHEET_EXTENSIONS else None,
            sheet_metadata=[sheet.model_dump() if hasattr(sheet, "model_dump") else sheet.dict() for sheet in sheets],
        )
        return result
    except ProcessingError as error:
        if not size_bytes:
            content_length = request.headers.get("content-length")
            if content_length and content_length.isdigit():
                size_bytes = int(content_length)
            else:
                size_bytes = session.size
        return _failure_result(filename, size_bytes, error)
    except Exception:
        return _failure_result(
            filename,
            size_bytes or session.size,
            ProcessingError("PROCESSING_FAILED", "문서 처리 중 오류가 발생했습니다. 다시 시도해 주세요.", 500),
        )
    finally:
        content = b""
        extracted = None
        session.clear()


def _download_response(content: bytes, filename: str, media_type: str) -> Response:
    safe_name = quote(filename, safe="")
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{safe_name}",
            "Cache-Control": "no-store",
        },
    )


def _result_filename(filename: str, extension: str) -> str:
    original_name = PurePosixPath(filename.replace("\\", "/")).name
    stem = PurePosixPath(original_name).stem or "sumnote_result"
    return f"{stem}_summary{extension}"


@router.post("/documents/download/pdf")
async def download_pdf(result: ProcessingResult) -> Response:
    content = build_pdf_report(result)
    name = _result_filename(result.document.filename, ".pdf")
    return _download_response(content, name, "application/pdf")


@router.post("/documents/download/xlsx")
async def download_xlsx(result: ProcessingResult) -> Response:
    if result.document.extension not in SPREADSHEET_EXTENSIONS:
        raise ProcessingError("XLSX_NOT_AVAILABLE", "스프레드시트 입력 결과만 XLSX로 다운로드할 수 있습니다.", 400)
    content = build_xlsx_report(result)
    name = _result_filename(result.document.filename, ".xlsx")
    return _download_response(
        content,
        name,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
