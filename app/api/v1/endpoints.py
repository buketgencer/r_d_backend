# app/api/v1/endpoints.py
# -----------------------------------------------------------
# /v1/process  → PDF + soru listesi alır, pipeline’i arka planda çalıştırır
# -----------------------------------------------------------

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import os
from typing import List
from pydantic import BaseModel

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    BackgroundTasks,
    HTTPException,
)

# ----- şema ve servis içe aktarımları ----------------------
from ...models.schemas import (
    QuestionRequest,
    ProcessResponse,
)
from ...services.pipeline_runner import run_pipeline  # uçtan uca pipeline
from ...core.config import get_settings

# -----------------------------------------------------------
st = get_settings()
router = APIRouter(prefix="/v1", tags=["pipeline"])
# -----------------------------------------------------------


# ==========  /process  =====================================
@router.post("/process", response_model=ProcessResponse)
async def process_report(
    bg: BackgroundTasks,
    questions: str = Form(..., description="JSON list of QuestionRequest"),
    pdf_file: UploadFile = File(..., description="PDF file to analyse"),
):
    """Arka planda run_pipeline’ı tetikler, anında işlem kimliği döndürür."""

    # 1) Soru listesi doğrulaması
    try:
        questions_data = json.loads(questions)
        _ = [QuestionRequest(**q) for q in questions_data]
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(400, f"Invalid questions payload: {exc}")

    # 2) PDF doğrulama
    if not pdf_file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only .pdf files are supported")

    # 3) Dosyaları kaydet
    upload_dir = Path("user_uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = upload_dir / pdf_file.filename
    pdf_path.write_bytes(await pdf_file.read())

    questions_path = upload_dir / "questions.json"
    questions_path.write_text(
        json.dumps(questions_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 4) Basit işlem kimliği (memory state tutulmuyor)
    job_id = str(uuid4())
    report_id = pdf_path.stem

    # 5) Pipeline’i arka planda başlat
    bg.add_task(
        run_pipeline,
        pdf_path=pdf_path,
        questions_path=questions_path,
        report_id=report_id,
        send_to_gpt=True,
    )

    # 6) Yanıt
    return ProcessResponse(
        job_id=job_id,
        report_id=report_id,
        count=len(questions_data),
        status="processing",
        results=[],  # <––– Bunu ekledik
    )

