from pydantic import BaseModel


class DocumentUploadResult(BaseModel):
    filename: str
    extension: str
    format: str
    size_bytes: int
    max_size_bytes: int
    format_check: str
    stored: bool
    message: str
