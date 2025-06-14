from pydantic import BaseModel, Field, model_validator

class ProcessRequest(BaseModel):
    report_id: str = Field(..., example="rapor2023")

    # ↓ isteğe bağlı yaptık
    question_id: int | None = Field(
        None, ge=1, description="Hazır soru numarası"
    )
    custom_question: str | None = Field(
        None, description="Kullanıcının kendi sorusu"
    )
    custom_yordam: str | None = Field(
        None, description="Kullanıcının kendi yordamı (opsiyonel)"
    )

    @model_validator(mode="after")
    def check_either_question(cls, values):
        """
        • question_id *ve* custom_question aynı anda verilemez
        • ikisinden *en az biri* verilmelidir
        """
        qid  = values.question_id
        cqs  = values.custom_question

        if (qid is None and not cqs) or (qid is not None and cqs):
            raise ValueError(
                "Either 'question_id' OR 'custom_question' must be provided,"
                " but not both."
            )
        return values


class ProcessResponse(BaseModel):
    job_id: str
    report_id: str
    question_id: int | None
    status: str
