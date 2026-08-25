import logging
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.schemas.analysis import (
    TextAnalysisRequest, URLAnalysisRequest, CombinedAnalysisRequest, AnalysisResponse
)
from app.ml.inference import predict_text, models_available as text_models_available
from app.url_analysis.inference import analyze_url
from app.risk_engine.engine import SignalInput, compute_overall_risk
from app.ai_investigator.investigator import investigate
from app.ocr.extractor import extract_text_from_bytes, OCRError
from app.core.config import settings

logger = logging.getLogger("scamshield.analysis")
router = APIRouter(prefix="/api/analyze", tags=["analysis"])


def _run_full_pipeline(text: str = None, url: str = None, ocr_meta: dict = None) -> AnalysisResponse:
    text_result = None
    url_result = None

    if text and text.strip():
        try:
            text_result = predict_text(text)
        except Exception as e:
            logger.exception("Text ML inference failed")
            raise HTTPException(status_code=500, detail=f"Text analysis failed: {e}")

    if url and url.strip():
        try:
            url_result = analyze_url(url.strip())
        except Exception as e:
            logger.exception("URL analysis failed")
            raise HTTPException(status_code=500, detail=f"URL analysis failed: {e}")

    signal = SignalInput(
        text_scam_probability=text_result["scam_probability"] if text_result else None,
        text_scam_type=text_result.get("scam_type") if text_result else None,
        text_scam_type_confidence=text_result.get("scam_type_confidence") if text_result else None,
        url_malicious_probability=url_result["malicious_probability"] if url_result else None,
        url_evidence=url_result["evidence"] if url_result else [],
        ocr_confidence=ocr_meta.get("ocr_confidence") if ocr_meta else None,
        text_top_terms=text_result.get("top_terms", []) if text_result else [],
    )
    risk_result = compute_overall_risk(signal)

    ai_result = investigate(risk_result, submitted_text=text or "", url_result=url_result)

    return AnalysisResponse(
        overall_risk_score=risk_result["overall_risk_score"],
        risk_level=risk_result["risk_level"],
        scam_category=risk_result["scam_category"],
        confidence=risk_result["confidence"],
        evidence=risk_result["evidence"],
        signals=risk_result["signals"],
        text_analysis=text_result,
        url_analysis=url_result,
        ocr=ocr_meta,
        ai_investigation=ai_result,
    )


@router.post("/text", response_model=AnalysisResponse)
def analyze_text(payload: TextAnalysisRequest):
    if not text_models_available():
        raise HTTPException(
            status_code=503,
            detail="ML models are not trained yet. Run `python -m app.ml.train_text_model` in the backend directory.",
        )
    return _run_full_pipeline(text=payload.text)


@router.post("/url", response_model=AnalysisResponse)
def analyze_url_endpoint(payload: URLAnalysisRequest):
    return _run_full_pipeline(url=payload.url)


@router.post("/combined", response_model=AnalysisResponse)
def analyze_combined(payload: CombinedAnalysisRequest):
    if not payload.text and not payload.url:
        raise HTTPException(status_code=400, detail="Provide at least text or a URL to analyze.")
    return _run_full_pipeline(text=payload.text, url=payload.url)


@router.post("/image", response_model=AnalysisResponse)
async def analyze_image(file: UploadFile = File(...)):
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(status_code=413, detail=f"File too large ({size_mb:.1f}MB). Max is {settings.MAX_UPLOAD_SIZE_MB}MB.")

    try:
        ocr_result = extract_text_from_bytes(contents)
    except OCRError as e:
        raise HTTPException(status_code=422, detail=str(e))

    extracted_text = ocr_result["extracted_text"]
    if not extracted_text:
        raise HTTPException(status_code=422, detail="No readable text was found in the image.")

    return _run_full_pipeline(text=extracted_text, ocr_meta=ocr_result)
