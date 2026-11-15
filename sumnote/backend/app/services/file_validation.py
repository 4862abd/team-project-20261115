from pathlib import PurePosixPath

from app.core.config import FORMAT_LABELS, MAX_UPLOAD_SIZE_BYTES, SUPPORTED_EXTENSIONS
from app.services.errors import UploadValidationError


def validate_filename(filename: str) -> tuple[str, str]:
    if not filename or not filename.strip():
        raise UploadValidationError(
            "FILENAME_REQUIRED",
            "파일 이름을 확인할 수 없습니다. 파일을 다시 선택해 주세요.",
            400,
        )

    normalized_name = filename.replace("\\", "/")
    extension = PurePosixPath(normalized_name).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise UploadValidationError(
            "UNSUPPORTED_FORMAT",
            f"지원하지 않는 파일 형식입니다. 현재 지원 형식: {supported}",
            415,
        )

    return extension, FORMAT_LABELS[extension]


def validate_upload_size(size_bytes: int) -> None:
    if size_bytes > MAX_UPLOAD_SIZE_BYTES:
        raise UploadValidationError(
            "FILE_TOO_LARGE",
            "파일 크기가 10MB를 초과했습니다. 10MB 이하 파일을 선택해 주세요.",
            413,
        )
