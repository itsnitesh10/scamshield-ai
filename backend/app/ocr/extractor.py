"""
OCR extraction module. Uses Tesseract (via pytesseract) to pull text out
of uploaded screenshots (WhatsApp, SMS, email, payment confirmations,
etc.) before it's handed to the same text-analysis pipeline used for
pasted text.

Includes light preprocessing (grayscale, upscaling, thresholding) to
improve OCR accuracy on typical phone-screenshot inputs.
"""
import io
import os
import shutil
from PIL import Image, ImageOps, ImageFilter
import pytesseract


class OCRError(Exception):
    pass


def _configure_tesseract_path():
    """
    Locates the Tesseract binary so pytesseract can find it, without ever
    hard-coding a personal/OS-specific path.

    Resolution order:
      1. TESSERACT_CMD env var, if set — used as-is (this is how Windows
         users point at their install, e.g.
         C:\\Program Files\\Tesseract-OCR\\tesseract.exe).
      2. Whatever `tesseract` already resolves to on PATH (normal on
         Linux/macOS after `apt install` / `brew install`).
      3. Neither found -> raise a clear, actionable OCRError instead of
         letting pytesseract's generic "not installed or not in PATH"
         error surface.
    """
    configured = os.getenv("TESSERACT_CMD", "").strip()
    if configured:
        if not os.path.isfile(configured):
            raise OCRError(
                f"TESSERACT_CMD is set to '{configured}' but no file exists at that path. "
                "Check the path in your .env file (e.g. "
                "TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe on Windows)."
            )
        pytesseract.pytesseract.tesseract_cmd = configured
        return

    on_path = shutil.which("tesseract")
    if on_path:
        pytesseract.pytesseract.tesseract_cmd = on_path
        return

    raise OCRError(
        "Tesseract executable was not found. Either add it to your system PATH, "
        "or set TESSERACT_CMD in backend/.env to the full path of tesseract.exe "
        "(e.g. TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe on Windows)."
    )


# Resolved once at import time so every request doesn't re-check the
# filesystem/env, but any OCRError here is only raised lazily the first
# time OCR is actually used (see extract_text_from_bytes), not at
# server startup, so a missing Tesseract install doesn't crash the app.
_tesseract_configured = False


def _ensure_tesseract_configured():
    global _tesseract_configured
    if not _tesseract_configured:
        _configure_tesseract_path()
        _tesseract_configured = True


def preprocess_image(image: Image.Image) -> Image.Image:
    img = image.convert("L")  # grayscale

    # upscale small screenshots for better OCR accuracy
    max_dim = max(img.size)
    if max_dim < 1200:
        scale = 1200 / max_dim
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)

    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.SHARPEN)
    return img


def extract_text_from_bytes(image_bytes: bytes) -> dict:
    _ensure_tesseract_configured()

    try:
        image = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        raise OCRError(f"Could not read image: {e}")

    try:
        processed = preprocess_image(image)
        raw_text = pytesseract.image_to_string(processed)
        data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT)
        confidences = [int(c) for c in data.get("conf", []) if str(c).lstrip("-").isdigit() and int(c) >= 0]
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    except OCRError:
        raise
    except pytesseract.TesseractNotFoundError as e:
        raise OCRError(
            "Tesseract was found but could not be run. If you're on Windows, double-check "
            f"TESSERACT_CMD points at the tesseract.exe file, not just its folder. ({e})"
        )
    except Exception as e:
        raise OCRError(f"OCR extraction failed: {e}")

    cleaned = "\n".join(line.strip() for line in raw_text.splitlines() if line.strip())

    return {
        "extracted_text": cleaned,
        "ocr_confidence": round(avg_conf, 2),
        "char_count": len(cleaned),
        "image_size": image.size,
    }
