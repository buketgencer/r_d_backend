# /v1/process route’u
#/v1/process – multipart PDF + form verisini alır, BackgroundTasks ile pipeline’ı tetikler
from http.client import HTTPException

from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends
from pathlib import Path
from ...models.schemas import ProcessRequest, ProcessResponse
from ...services.pipeline_runner import run_pipeline
from ...services import state

router = APIRouter(prefix="/v1", tags=["pipeline"])

@router.post("/process", response_model=ProcessResponse)
def process_report(
        bg: BackgroundTasks,
        req: ProcessRequest = Depends(),
        pdf: UploadFile = File(...)
):
    job_id = state.new_job()            # ★ 1) kayıt
    temp_path = Path("user_uploads") / pdf.filename
    temp_path.parent.mkdir(exist_ok=True, parents=True)
    with temp_path.open("wb") as f:
        f.write(pdf.file.read())

    bg.add_task(
        run_pipeline,
        pdf_path=temp_path,
        report_id=req.report_id,
        question_id=req.question_id,
        custom_question=req.custom_question,
        custom_yordam=req.custom_yordam,
        job_id=job_id
    )

    return ProcessResponse(
        job_id=job_id,
        report_id=req.report_id,
        question_id=req.question_id,
        status="processing"
    )              # Python 3.9 dict birleştirme

# add the new endpoint
# ---------- status ----------
@router.get("/status/{job_id}")
def job_status(job_id: str):
    data = state.get(job_id)
    if not data:
        raise HTTPException(404, "Job not found")
    return data
