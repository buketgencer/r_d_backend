# /v1/process route’u
#/v1/process – multipart PDF + form verisini alır, BackgroundTasks ile pipeline’ı tetikler
from http.client import HTTPException

from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, HTTPException, Form
from pathlib import Path
from ...models.schemas import ProcessRequest, ProcessResponse, ProcessResult, QuestionRequest
from ...services.pipeline_runner import run_pipeline
from ...services import state
import json

router = APIRouter(prefix="/v1", tags=["pipeline"])

# @router.post("/process", response_model=ProcessResponse)
# async def process_report(
#         bg: BackgroundTasks,
#         req: ProcessRequest = Depends(),
#         pdf: UploadFile = File(...),
# ):
#     job_id = state.new_job()

#     temp_path = Path("user_uploads") / pdf.filename
#     temp_path.parent.mkdir(parents=True, exist_ok=True)
#     temp_path.write_bytes(await pdf.read())

#     bg.add_task(
#         run_pipeline,
#         pdf_path=temp_path,
#         report_id=req.report_id,
#         question_id=req.question_id,          # None gelebilir
#         custom_question=req.custom_question,
#         custom_yordam=req.custom_yordam,
#         job_id=job_id,
#     )

#     return ProcessResponse(
#         job_id=job_id,
#         report_id=req.report_id,
#         question_id=req.question_id,
#         status="processing",
#     )
# add the new endpoint

# ------------- process -------------
@router.post("/process", response_model=ProcessResponse)
async def process(
    request: str = Form(...),
    pdf_file: UploadFile = File(...)
):
    try:
        process_request = ProcessRequest.model_validate_json(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request format: {str(e)}")
    
    if pdf_file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    pdf_content = await pdf_file.read()

    print(process_request)
    print(pdf_content)

    # write pdf to the file system
    pdf_path = Path("user_uploads") / pdf_file.filename
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(pdf_content)
    
    results = []
    for question_req in process_request.questions:
        result = ProcessResult(
            question=question_req.soru,
            answer="Sample answer from PDF processing",
            status="answer_found"
        )
        results.append(result)
    
    response = ProcessResponse(
        results=results,
        count=len(results)
    )
    
    return response
# ---------- status ----------
@router.get("/status/{job_id}")
def job_status(job_id: str):
    data = state.get(job_id)
    if not data:
        raise HTTPException(404, "Job not found")
    return data
