from pydantic import BaseModel, Field
from typing import Literal

from app.api.schemas.document import DocumentInfo


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class Evidence(BaseModel):
    quote: str = ""
    location: str = "없음"


class KeyPoint(BaseModel):
    level: str = "대단락"
    importance: str = "중간"
    title: str = ""
    content: str = ""
    evidence: list[Evidence] = Field(default_factory=list)


class ImportantFact(BaseModel):
    label: str = ""
    value: str = ""
    importance: str = "중간"
    evidence: list[Evidence] = Field(default_factory=list)


class SheetSummary(BaseModel):
    sheet_name: str = ""
    content: str = ""
    evidence: list[Evidence] = Field(default_factory=list)


class SummaryData(BaseModel):
    title: str = ""
    one_line_summary: str = ""
    overview: str = ""
    topics: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    key_points: list[KeyPoint] = Field(default_factory=list)
    important_facts: list[ImportantFact] = Field(default_factory=list)
    sheet_summaries: list[SheetSummary] = Field(default_factory=list)
    conclusion: str = ""


class VerificationItem(BaseModel):
    category: str = "확인 필요"
    importance: str = "중간"
    issue: str = ""
    reason: str = ""
    status: str = "사람 확인 필요"
    evidence: list[Evidence] = Field(default_factory=list)


class VerificationData(BaseModel):
    generated: bool = False
    status: str = "생성되지 않음"
    items: list[VerificationItem] = Field(default_factory=list)


class ProcessingResult(BaseModel):
    document: DocumentInfo
    status: Literal["completed", "needs_review", "failed", "no_result"]
    status_message: str
    summary: SummaryData = Field(default_factory=SummaryData)
    verification: VerificationData = Field(default_factory=VerificationData)
