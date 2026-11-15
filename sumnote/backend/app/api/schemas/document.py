from pydantic import BaseModel, Field


class SheetInfo(BaseModel):
    name: str
    headers: list[str] = Field(default_factory=list)
    data_row_count: int = 0


class DocumentInfo(BaseModel):
    filename: str
    extension: str
    format: str
    size_bytes: int = 0
    page_count: int | None = None
    sheet_count: int | None = None
    sheets: list[SheetInfo] = Field(default_factory=list)


class DocumentUploadResult(BaseModel):
    filename: str
    extension: str
    format: str
    size_bytes: int
    max_size_bytes: int
    format_check: str
    stored: bool
    message: str
