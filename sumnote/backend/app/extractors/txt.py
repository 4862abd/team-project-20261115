from app.services.errors import ProcessingError
from app.services.text_normalization import ExtractedDocument, normalize_text


def _decode_text(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp949", "utf-16"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ProcessingError(
        "TEXT_ENCODING_UNSUPPORTED",
        "TXT 파일의 문자 인코딩을 읽을 수 없습니다. UTF-8 또는 CP949로 저장한 뒤 다시 시도해 주세요.",
        422,
    )


def extract_txt(data: bytes) -> ExtractedDocument:
    text = normalize_text(_decode_text(data))
    if not text:
        return ExtractedDocument(text="")

    numbered_lines = [f"[TXT 줄 {index}] {line}" for index, line in enumerate(text.splitlines(), start=1)]
    return ExtractedDocument(text="\n".join(numbered_lines))
