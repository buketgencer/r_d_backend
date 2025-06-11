# Pydantic istek/yanıt şemaları

from pydantic import BaseModel, Field

class ProcessRequest(BaseModel):
    report_id: str = Field(..., example="rapor2023")

    question_id: int = Field(..., ge=1)

    custom_question: str | None = None

    custom_yordam:   str | None = None

class ProcessResponse(BaseModel):
    job_id: str
    report_id: str
    question_id: int
    status: str
