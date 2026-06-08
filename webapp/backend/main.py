"""FastAPI backend for Invoice Reliability Assessment Agent."""
import sys
import os

sys.path.insert(0, '/home/user/Agent-Studio')

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from invoice_service import (
    assess_json_file,
    assess_image_file,
    assess_pdf_file,
    assess_invoice_data,
)

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = FastAPI(
    title="Invoice Reliability Assessment API",
    description="AI-powered invoice authenticity and compliance analysis",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_CONTENT_TYPES = {
    "application/json": "json",
    "application/pdf": "pdf",
    "image/jpeg": "image",
    "image/jpg": "image",
    "image/png": "image",
    "image/webp": "image",
}

SAMPLE_NAMES = ["clean", "duplicate", "unknown_vendor", "over_threshold", "bad_arithmetic", "foreign_currency"]


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    api_key_present = bool(os.environ.get("ANTHROPIC_API_KEY", ""))
    return {
        "status": "ok",
        "service": "Invoice Reliability Assessment API",
        "version": "1.0.0",
        "claude_enabled": api_key_present,
        "mode": "claude" if api_key_present else "mock",
    }


@app.get("/api/samples")
async def list_samples():
    """Return list of available sample invoice names."""
    return {
        "samples": SAMPLE_NAMES,
        "descriptions": {
            "clean": "Clean, compliant invoice from a known vendor",
            "duplicate": "Invoice that matches a known duplicate in the system",
            "unknown_vendor": "Invoice from an unregistered vendor",
            "over_threshold": "Invoice exceeding policy approval thresholds",
            "bad_arithmetic": "Invoice with arithmetic inconsistencies",
            "foreign_currency": "Invoice in foreign currency (EUR) over threshold",
        },
    }


@app.post("/api/assess")
async def assess_uploaded_invoice(file: UploadFile = File(...)):
    """
    Accept a file upload (PDF, image, JSON) and return an assessment JSON.
    """
    content_type = file.content_type or ""
    filename = file.filename or ""

    # Determine file type
    file_type = ALLOWED_CONTENT_TYPES.get(content_type)

    # Fallback: guess from filename extension
    if not file_type:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        ext_map = {"json": "json", "pdf": "pdf", "jpg": "image", "jpeg": "image", "png": "image", "webp": "image"}
        file_type = ext_map.get(ext)

    if not file_type:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {content_type or filename}. Accepted: PDF, JPEG, PNG, JSON",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        if file_type == "json":
            result = assess_json_file(content)
        elif file_type == "image":
            # Normalise content type
            ct = content_type if content_type.startswith("image/") else "image/jpeg"
            result = assess_image_file(content, ct)
        elif file_type == "pdf":
            result = assess_pdf_file(content)
        else:
            raise HTTPException(status_code=415, detail="Unsupported file type")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(exc)}") from exc

    return JSONResponse(content=result)


@app.post("/api/assess/sample/{name}")
async def assess_sample_invoice(name: str):
    """Run assessment on a built-in sample invoice."""
    if name not in SAMPLE_NAMES:
        raise HTTPException(
            status_code=404,
            detail=f"Sample '{name}' not found. Available: {SAMPLE_NAMES}",
        )

    try:
        from invoice_checker.sample_invoices import get_sample
        invoice_data = get_sample(name)
        result = assess_invoice_data(invoice_data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(exc)}") from exc

    return JSONResponse(content=result)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
