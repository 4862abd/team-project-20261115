from html import escape
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.api.schemas.result import ProcessingResult
from app.core.config import PDF_FONT_PATH
from app.services.errors import ProcessingError


FONT_NAME = "SumNoteKorean"


def _register_font() -> str:
    if FONT_NAME in pdfmetrics.getRegisteredFontNames():
        return FONT_NAME

    font_candidates = [
        PDF_FONT_PATH,
        r"C:\Windows\Fonts\malgun.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansKR-Regular.ttf",
    ]
    for candidate in font_candidates:
        if candidate and Path(candidate).is_file():
            try:
                pdfmetrics.registerFont(TTFont(FONT_NAME, candidate))
                pdfmetrics.registerFontFamily(FONT_NAME, normal=FONT_NAME, bold=FONT_NAME, italic=FONT_NAME, boldItalic=FONT_NAME)
                return FONT_NAME
            except Exception:
                continue
    raise ProcessingError(
        "PDF_FONT_NOT_FOUND",
        "PDF용 한글 글꼴을 찾지 못했습니다. SUMNOTE_PDF_FONT_PATH에 한글 TTF 글꼴 경로를 설정해 주세요.",
        500,
    )


def _paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    safe = escape(text or "없음").replace("\n", "<br/>")
    return Paragraph(safe, style)


def _status_label(status: str) -> str:
    return {
        "completed": "완료",
        "needs_review": "일부 근거 확인 필요",
        "failed": "실패",
        "no_result": "결과 없음",
    }.get(status, status or "없음")


def build_pdf_report(result: ProcessingResult) -> bytes:
    font_name = _register_font()
    buffer = BytesIO()
    document = result.document

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "SumNoteTitle", parent=styles["Title"], fontName=font_name, fontSize=20, leading=27,
        textColor=colors.HexColor("#172238"), alignment=TA_LEFT, spaceAfter=5 * mm,
    )
    heading_style = ParagraphStyle(
        "SumNoteHeading", parent=styles["Heading2"], fontName=font_name, fontSize=13, leading=18,
        textColor=colors.HexColor("#315de8"), spaceBefore=5 * mm, spaceAfter=2 * mm,
    )
    body_style = ParagraphStyle(
        "SumNoteBody", parent=styles["BodyText"], fontName=font_name, fontSize=9.5, leading=15,
        textColor=colors.HexColor("#273247"), alignment=TA_LEFT, spaceAfter=2.5 * mm,
    )
    small_style = ParagraphStyle(
        "SumNoteSmall", parent=body_style, fontSize=8.5, leading=12,
        textColor=colors.HexColor("#59657a"), leftIndent=4 * mm,
    )

    elements = [
        _paragraph(result.summary.title or document.filename or "문서 요약", title_style),
        _paragraph(f"문서명: {document.filename}", body_style),
        _paragraph(f"입력 형식: {document.format} ({document.extension})", body_style),
        _paragraph(f"파일 크기: {document.size_bytes:,} bytes", body_style),
        _paragraph(f"처리 상태: {_status_label(result.status)}", body_style),
        _paragraph(result.status_message, body_style),
    ]
    if document.page_count is not None:
        elements.append(_paragraph(f"페이지 수: {document.page_count}", body_style))
    if document.sheet_count is not None:
        elements.append(_paragraph(f"표시 시트 수: {document.sheet_count}", body_style))
        for sheet in document.sheets:
            elements.append(
                _paragraph(
                    f"시트: {sheet.name} · 헤더: {', '.join(sheet.headers) or '없음'} · 데이터 행: {sheet.data_row_count}",
                    small_style,
                )
            )

    summary = result.summary
    elements.extend([
        _paragraph("한 줄 요약", heading_style),
        _paragraph(summary.one_line_summary, body_style),
        _paragraph("문서 개요", heading_style),
        _paragraph(summary.overview, body_style),
        _paragraph("주제", heading_style),
        _paragraph(", ".join(summary.topics), body_style),
        _paragraph("키워드", heading_style),
        _paragraph(", ".join(summary.keywords), body_style),
        _paragraph("핵심 내용", heading_style),
    ])

    importance_order = {"높음": 0, "중간": 1, "낮음": 2}
    key_points = sorted(summary.key_points, key=lambda item: importance_order.get(item.importance, 1))
    for point in key_points:
        elements.append(_paragraph(f"{point.level} · {point.importance} · {point.title}", body_style))
        elements.append(_paragraph(point.content, small_style))

    elements.append(_paragraph("주요 인물·기관·날짜·수치·조건", heading_style))
    if summary.important_facts:
        for fact in sorted(summary.important_facts, key=lambda item: importance_order.get(item.importance, 1)):
            elements.append(_paragraph(f"{fact.label}: {fact.value} ({fact.importance})", body_style))
    else:
        elements.append(_paragraph("없음", body_style))

    elements.extend([
        _paragraph("결론 또는 핵심 메시지", heading_style),
        _paragraph(summary.conclusion, body_style),
        _paragraph("원문 근거", heading_style),
    ])
    evidence_items = []
    for point in summary.key_points:
        for evidence in point.evidence:
            evidence_items.append((point.title, evidence.quote, evidence.location))
    for fact in summary.important_facts:
        for evidence in fact.evidence:
            evidence_items.append((fact.label, evidence.quote, evidence.location))
    if evidence_items:
        for label, quote, location in evidence_items:
            elements.append(_paragraph(f"{label} · 위치: {location}", body_style))
            elements.append(_paragraph(quote, small_style))
    else:
        elements.append(_paragraph("없음", body_style))

    elements.append(_paragraph("사람이 확인할 검토 항목", heading_style))
    if not result.verification.generated:
        elements.append(_paragraph("검증 결과 없음", body_style))
    elif not result.verification.items:
        elements.append(_paragraph("없음", body_style))
    else:
        for index, item in enumerate(result.verification.items, start=1):
            elements.append(_paragraph(f"{index}. [{item.importance}] {item.category}: {item.issue}", body_style))
            elements.append(_paragraph(f"검토 이유: {item.reason}", small_style))
            if item.evidence:
                for evidence in item.evidence:
                    elements.append(_paragraph(f"원문 근거 · 위치: {evidence.location}", small_style))
                    elements.append(_paragraph(evidence.quote, small_style))
            else:
                elements.append(_paragraph("원문 근거: 없음", small_style))

    def draw_page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont(font_name, 8)
        canvas.setFillColor(colors.HexColor("#69758b"))
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"페이지 {doc.page}")
        canvas.restoreState()

    try:
        pdf = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=17 * mm,
            bottomMargin=18 * mm,
            title=summary.title or document.filename,
            author="sumnote",
        )
        pdf.build(elements, onFirstPage=draw_page_number, onLaterPages=draw_page_number)
        return buffer.getvalue()
    except ProcessingError:
        raise
    except Exception as error:
        raise ProcessingError("PDF_GENERATION_FAILED", "PDF 결과 파일을 만들지 못했습니다.", 500) from error
