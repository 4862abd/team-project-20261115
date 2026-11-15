from pathlib import Path


MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
FORMAT_LABELS = {
    ".pdf": "PDF 문서",
    ".txt": "TXT 텍스트",
    ".docx": "Word 문서",
    ".xlsx": "Excel 통합 문서",
    ".xls": "Excel 97–2003 통합 문서",
    ".csv": "CSV 데이터",
}
SUPPORTED_EXTENSIONS = set(FORMAT_LABELS)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_DIRECTORY = PROJECT_ROOT / "frontend"
