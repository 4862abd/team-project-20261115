from fastapi import APIRouter, Query, Request

from app.api.schemas.document import DocumentUploadResult
from app.core.config import MAX_UPLOAD_SIZE_BYTES
from app.services.errors import UploadValidationError
from app.services.file_validation import validate_filename, validate_upload_size


router = APIRouter()


async def _count_upload_bytes(request: Request) -> int:
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            declared_size = int(content_length)
        except ValueError as error:
            raise UploadValidationError(
                "INVALID_CONTENT_LENGTH",
                "업로드 크기를 확인할 수 없습니다.",
                400,
            ) from error
        validate_upload_size(declared_size)

    received_size = 0
    async for chunk in request.stream():
        received_size += len(chunk)
        validate_upload_size(received_size)

    return received_size


@router.post("/documents/validate", response_model=DocumentUploadResult)
async def upload_and_check_format(
    request: Request,
    filename: str = Query(default=""),
) -> DocumentUploadResult:
    size_bytes = await _count_upload_bytes(request)
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
