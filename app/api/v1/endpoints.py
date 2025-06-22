# app/api/v1/endpoints.py
# -----------------------------------------------------------
# /v1/process  → PDF + soru listesi alır, pipeline’i arka planda çalıştırır
# /v1/status   → job durumunu döndürür
# -----------------------------------------------------------

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

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
    ProcessResult,
    ProcessResponse,
)
from ...services import state                        # basit job store
from ...services.pipeline_runner import run_pipeline # yeni pipeline
from ...core.config import get_settings              # .env ayarları

# -----------------------------------------------------------
st = get_settings()          # OPENAI_API_KEY, WORKSPACE_ROOT, TOPK vb.
router = APIRouter(prefix="/v1", tags=["pipeline"])
# -----------------------------------------------------------


# ==========  /process  =====================================
@router.post("/process", response_model=ProcessResponse)
async def process_report(
    bg: BackgroundTasks,
    questions: str = Form(..., description="JSON list of QuestionRequest"),
    pdf_file: UploadFile = File(..., description="PDF file to analyse"),
):
    """
    • PDF + JSON soru listesi alır.
    • Dosyaları `user_uploads/` dizinine yazar.
    • pipeline_runner.run_pipeline()’ı arka planda tetikler.
    • Hemen bir job_id döndürür; sonuçları /status ile sorgulanır.
    """
    # ----------- 1) Soru listesi doğrulaması ----------------
    try:
        questions_data = json.loads(questions)
        _ = [QuestionRequest(**q) for q in questions_data]  # şema doğrulama
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(400, f"Invalid questions payload: {exc}")

    # ----------- 2) PDF doğrulama ---------------------------
    if not pdf_file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only .pdf files are supported")

    upload_dir = Path("user_uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = upload_dir / pdf_file.filename
    pdf_path.write_bytes(await pdf_file.read())           # senk. kaydet

    questions_path = upload_dir / "questions.txt"
    questions_path.write_text(
        json.dumps(questions_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # ----------- 3) Job ID oluştur & durum kaydet -----------
    job_id = state.new_job()
    report_id = pdf_path.stem

    state.update(job_id, {
        "status": "queued",
        "report_id": report_id,
        "pdf": str(pdf_path),
        "questions": str(questions_path),
    })

    # ----------- 4) Pipeline’i arka planda başlat -----------
    bg.add_task(
        _run_pipeline_bg,
        job_id=job_id,
        pdf_path=pdf_path,
        questions_path=questions_path,
        report_id=report_id,
    )

    # ----------- 5) Anında yanıt ----------------------------
    return ProcessResponse(
        job_id=job_id,
        report_id=report_id,
        count=len(questions_data),
        status="processing",
    )


# ==========  Background worker =============================
def _run_pipeline_bg(job_id: str, pdf_path: Path, questions_path: Path, report_id: str):
    """
    state modülüne job durumunu yazarak run_pipeline’ı çalıştırır.
    """
    try:
        state.update(job_id, {"status": "processing"})
        run_pipeline(
            pdf_path=pdf_path,
            questions_path=questions_path,
            report_id=report_id,
            send_to_gpt=True,                 # .env → OPENAI_API_KEY gerekli
        )
        state.update(job_id, {"status": "completed"})
    except Exception as exc:
        state.update(job_id, {"status": "failed", "error": str(exc)})


# ==========  /status  ======================================
@router.get("/status/{job_id}")
def job_status(job_id: str):
    """
    İşin son durumunu döndürür.  state modülü bellekte saklıyor
    (persistent bir store kullanıyorsanız burayı değiştirin).
    """
    data = state.get(job_id)
    if not data:
        raise HTTPException(404, "Job not found")
    return data
