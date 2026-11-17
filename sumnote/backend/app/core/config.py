import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env.example")

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
MAX_VISIBLE_SHEETS = 10
ANALYSIS_CHUNK_CHAR_LIMIT = 12_000
AIAGENT_TIMEOUT_SECONDS = float(os.getenv("AIAGENT_TIMEOUT_SECONDS", "90"))

FORMAT_LABELS = {
    ".pdf": "PDF 문서",
    ".txt": "TXT 텍스트",
    ".docx": "Word 문서",
    ".xlsx": "Excel 통합 문서",
    ".xls": "Excel 97-2003 통합 문서",
    ".csv": "CSV 데이터",
}
SUPPORTED_EXTENSIONS = set(FORMAT_LABELS)

AIAGENT_API_URL = os.getenv("AIAGENT_API_URL", "").strip()
AIAGENT_API_KEY = os.getenv("AIAGENT_API_KEY", "").strip()
AIAGENT_MODEL = os.getenv("AIAGENT_MODEL", "").strip()
PDF_FONT_PATH = os.getenv("SUMNOTE_PDF_FONT_PATH", "").strip()
