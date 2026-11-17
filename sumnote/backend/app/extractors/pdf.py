from io import BytesIO

from pypdf import PdfReader

from app.services.errors import ProcessingError
from app.services.text_normalization import ExtractedDocument, normalize_text


def extract_pdf(data: bytes) -> ExtractedDocument:
    try:
        reader = PdfReader(BytesIO(data), strict=False)
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception as error:
                raise ProcessingError(
                    "PDF_ENCRYPTED",
                    "암호화된 PDF는 읽을 수 없습니다. 암호를 해제한 뒤 다시 시도해 주세요.",
                    422,
                ) from error

        page_count = len(reader.pages)
        page_texts = []
        for index, page in enumerate(reader.pages, start=1):
            page_text = normalize_text(page.extract_text() or "")
            if page_text:
                page_texts.append(f"[PDF 페이지 {index}]\n{page_text}")
        if not page_texts:
            raise ProcessingError(
                "PDF_TEXT_NOT_FOUND",
                "PDF에서 텍스트를 찾지 못했습니다. 스캔 이미지 PDF는 OCR을 지원하지 않습니다.",
                422,
            )
        return ExtractedDocument(text="\n\n".join(page_texts), page_count=page_count)
    except ProcessingError:
        raise
    except Exception as error:
        raise ProcessingError(
            "PDF_READ_FAILED",
            "PDF 파일을 읽지 못했습니다. 파일이 손상되지 않았는지 확인해 주세요.",
            422,
        ) from error
