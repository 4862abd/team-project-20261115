from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.documents import router as documents_router
from app.core.config import FRONTEND_DIRECTORY
from app.services.errors import UploadValidationError


app = FastAPI(
    title="sumnote",
    description="문서 업로드 및 지원 확장자 확인",
    version="0.1.0",
)

app.include_router(documents_router, prefix="/api")


@app.exception_handler(UploadValidationError)
async def upload_validation_error_handler(
    request: Request,
    error: UploadValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={"error": {"code": error.code, "message": error.message}},
    )


app.mount("/", StaticFiles(directory=FRONTEND_DIRECTORY, html=True), name="frontend")
