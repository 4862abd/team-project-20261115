from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from app.api.schemas.result import ProcessingResult
from app.services.errors import ProcessingError


MAX_CELL_TEXT = 30_000


def _split_text(value: str) -> list[str]:
    value = value or "없음"
    if len(value) <= MAX_CELL_TEXT:
        return [value]
    return [value[index : index + MAX_CELL_TEXT] for index in range(0, len(value), MAX_CELL_TEXT)]


def _status_label(status: str) -> str:
    return {
        "completed": "완료",
        "needs_review": "일부 근거 확인 필요",
        "failed": "실패",
        "no_result": "결과 없음",
    }.get(status, status or "없음")


def _sheet_evidence_matches(item, sheet_name: str) -> bool:
    return any(sheet_name.casefold() in evidence.location.casefold() for evidence in item.evidence)


def build_xlsx_report(result: ProcessingResult) -> bytes:
    try:
        workbook = Workbook()
        overall = workbook.active
        overall.title = "전체 요약"
        per_sheet = workbook.create_sheet("시트별 요약")

        overall.append(["항목", "요약 내용", "검증 결과"])
        summary = result.summary
        status = _status_label(result.status)

        def add_summary_row(label: str, content: str, verification: str = "없음") -> None:
            pieces = _split_text(content)
            for index, piece in enumerate(pieces):
                overall.append([label if index == 0 else f"{label} (계속)", piece, verification if index == 0 else ""])

        add_summary_row("문서명", result.document.filename)
        add_summary_row("입력 형식", f"{result.document.format} ({result.document.extension})")
        add_summary_row("처리 상태", result.status_message, status)
        add_summary_row("한 줄 요약", summary.one_line_summary)
        add_summary_row("문서 개요", summary.overview)
        add_summary_row("주제", ", ".join(summary.topics))
        add_summary_row("키워드", ", ".join(summary.keywords))

        point_order = {"높음": 0, "중간": 1, "낮음": 2}
        for point in sorted(summary.key_points, key=lambda item: point_order.get(item.importance, 1)):
            add_summary_row(
                f"{point.level} · {point.importance} · {point.title}",
                point.content,
                "사람 확인 필요" if not point.evidence else "근거 연결됨",
            )
        for fact in sorted(summary.important_facts, key=lambda item: point_order.get(item.importance, 1)):
            add_summary_row(
                f"수치·조건 · {fact.label}",
                fact.value,
                "사람 확인 필요" if not fact.evidence else "근거 연결됨",
            )
        add_summary_row("결론 또는 핵심 메시지", summary.conclusion)

        if not result.verification.generated:
            add_summary_row("검증 결과", "검증 결과 없음", "검증 결과 없음")
        elif result.verification.items:
            for item in result.verification.items:
                evidence = "\n".join(
                    f"{entry.quote} (위치: {entry.location})" for entry in item.evidence
                ) or "없음"
                add_summary_row(
                    f"검토 항목 · {item.category} · {item.importance}",
                    f"{item.issue}\n검토 이유: {item.reason}\n원문 근거: {evidence}",
                    "사람 확인 필요",
                )
        else:
            add_summary_row("검증 결과", "없음", "완료")

        per_sheet.append(["원본 시트명", "헤더", "데이터 행 수", "주요 내용", "검증 결과"])
        sheet_points = summary.key_points
        sheet_summaries = {item.sheet_name.casefold(): item for item in summary.sheet_summaries}
        for source_sheet in result.document.sheets:
            sheet_summary = sheet_summaries.get(source_sheet.name.casefold())
            matching_points = [point for point in sheet_points if _sheet_evidence_matches(point, source_sheet.name)]
            matching_reviews = [
                item for item in result.verification.items
                if _sheet_evidence_matches(item, source_sheet.name)
            ]
            major_content = (
                sheet_summary.content
                if sheet_summary and sheet_summary.content
                else "\n".join(f"{point.title}: {point.content}" for point in matching_points) or "없음"
            )
            review_text = "\n".join(f"{item.category}: {item.issue}" for item in matching_reviews)
            if not result.verification.generated:
                review_text = "검증 결과 없음"
            elif not review_text:
                review_text = "없음"
            per_sheet.append([
                source_sheet.name,
                ", ".join(source_sheet.headers) or "없음",
                source_sheet.data_row_count,
                major_content,
                review_text,
            ])
        if not result.document.sheets:
            per_sheet.append(["없음", "없음", 0, "없음", "검증 결과 없음" if not result.verification.generated else "없음"])

        header_fill = PatternFill("solid", fgColor="315DE8")
        header_font = Font(color="FFFFFF", bold=True)
        for worksheet in (overall, per_sheet):
            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = worksheet.dimensions
            worksheet.sheet_view.showGridLines = False
            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(vertical="center", wrap_text=True)
            for row in worksheet.iter_rows(min_row=2):
                for cell in row:
                    cell.alignment = Alignment(vertical="top", wrap_text=True)
                    if isinstance(cell.value, str):
                        cell.data_type = "s"
            worksheet.row_dimensions[1].height = 28

        for column_index, width in enumerate((24, 78, 28), start=1):
            overall.column_dimensions[get_column_letter(column_index)].width = width
        for column_index, width in enumerate((24, 44, 18, 72, 58), start=1):
            per_sheet.column_dimensions[get_column_letter(column_index)].width = width

        buffer = BytesIO()
        workbook.save(buffer)
        workbook.close()
        return buffer.getvalue()
    except ProcessingError:
        raise
    except Exception as error:
        raise ProcessingError("XLSX_GENERATION_FAILED", "XLSX 결과 파일을 만들지 못했습니다.", 500) from error
