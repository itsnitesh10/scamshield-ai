import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.rate_limit import RateLimitMiddleware
from app.api.analysis import router as analysis_router
from app.ml.inference import models_available

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scamshield")

app = FastAPI(
    title=settings.APP_NAME,
    description="Multimodal scam detection & intelligence platform API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)

app.include_router(analysis_router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "text_models_loaded": models_available(),
        "llm_provider": settings.LLM_PROVIDER,
    }


@app.get("/")
def root():
    return {"message": "ScamShield AI backend is running. See /docs for API documentation."}
