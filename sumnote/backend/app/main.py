from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.documents import router as documents_router
from app.services.errors import ProcessingError


app = FastAPI(
    title="sumnote",
    description="문서 추출, AI 요약·검증, 결과 표시와 파일 다운로드",
    version="0.2.0",
)

app.include_router(documents_router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(ProcessingError)
async def upload_validation_error_handler(
    request: Request,
    error: ProcessingError,
) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={"error": {"code": error.code, "message": error.message}},
    )


@app.middleware("http")
async def prevent_response_caching(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response
