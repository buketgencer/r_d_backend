# app/api/v1/endpoints.py
# -----------------------------------------------------------
# /v1/process  → PDF + soru listesi alır, pipeline’i arka planda çalıştırır
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
    #BackgroundTasks,
    HTTPException,
)

# ----- şema ve servis içe aktarımları ----------------------
from ...models.schemas import (
    QuestionRequest,
    ProcessResponse,
    PreProcessResponse,
    ProcessResult,
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
    #bg: BackgroundTasks,
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
    '''
    bg.add_task(
        run_pipeline,
        pdf_path=pdf_path,
        questions_path=questions_path,
        report_id=report_id,
        send_to_gpt=True,
    )
    '''

    run_pipeline(
        pdf_path=pdf_path,
        questions_path=questions_path,
        report_id=report_id,
        send_to_gpt=True,  # varsayılan olarak cevap al
    )

    # 6) Yanıt – cevapları oku ve results alanını doldur
    answers_dir = Path("workspace") / report_id / "ANSWERS"
    results = []

    
    if answers_dir.exists():
        for answer_file in sorted(answers_dir.glob("answer_*.json")):
            with open(answer_file, "r", encoding="utf-8") as f:
                a = json.load(f)
                status = "answer_found" if a.get("cevap") and "bilgi bulunamadı" not in a.get("cevap", "").lower() else "answer_notfound"
                results.append(ProcessResult(
                    question=a.get("soru", ""),
                    answer=a.get("cevap", ""),
                    status=status
                ))
    
    return ProcessResponse(
        job_id=job_id,
        report_id=report_id,
        count=len(questions_data),
        status="completed" if results else "processing",
        results=results,
    )

# ==========  /process  =====================================
# Hedef dizin tek yerde dursun
UPLOAD_DIR = Path(r"C:\Users\user\Desktop\RD_PROJECT\r_d_backend\user_uploads")

@router.post("/preprocess-pdf", response_model=PreProcessResponse)
async def preprocess_report(
    pdf_file: UploadFile = File(..., description="PDF file to analyse")
):
    """
    Receive a PDF via multipart/form-data, save it to UPLOAD_DIR,
    and return a simple status response.
    """
    # Klasör yoksa oluştur
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Dosya adını temizle/validasyon (örn. ‘..’ vb. saldırıları engelle)
    filename = pdf_file.filename
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    target_path = UPLOAD_DIR / filename

    # Aynı adla dosya varsa hata döndür
    if target_path.exists():
        raise HTTPException(
            status_code=409,
            detail=f"File '{filename}' already exists in uploads directory",
        )

    try:
        # Dosyayı okuyup diske yaz
        file_bytes = await pdf_file.read()
        with open(target_path, "wb") as f:
            f.write(file_bytes)
        return PreProcessResponse(
            status="completed",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save PDF: {str(exc)}",
        ) from exc
    
    # (todo) yeni bir endpint ekleneck silme için filename alır input return status


    
