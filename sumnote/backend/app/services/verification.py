from app.api.schemas.result import SummaryData, VerificationData


def determine_result_status(
    summary: SummaryData,
    verification: VerificationData,
) -> tuple[str, str]:
    summary_exists = any(
        [
            summary.one_line_summary,
            summary.overview,
            summary.topics,
            summary.keywords,
            summary.key_points,
            summary.important_facts,
        ]
    )
    if not summary_exists:
        return "no_result", "요약 결과를 생성하지 못했습니다. 파일을 확인한 뒤 다시 시도해 주세요."

    evidence_missing = any(not point.evidence for point in summary.key_points)
    evidence_missing = evidence_missing or any(not fact.evidence for fact in summary.important_facts)

    if not verification.generated:
        return "needs_review", "요약은 생성했지만 검증 결과가 없습니다. 내용을 직접 확인해 주세요."
    if verification.items or evidence_missing:
        return "needs_review", "일부 내용이나 근거를 사람이 확인해야 합니다."
    return "completed", "요약과 검토 결과가 준비되었습니다."
