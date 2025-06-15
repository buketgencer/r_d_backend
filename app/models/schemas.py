from typing import List, Literal
from pydantic import BaseModel, Field

class QuestionRequest(BaseModel):
    """Schema for individual question request"""
    soru: str = Field(..., description="The question text")
    yordam: str | None = Field(None, description="Optional custom method")

class ProcessRequest(BaseModel):
    """Schema for process request"""
    questions: List[QuestionRequest] = Field(..., description="List of questions to process")

class ProcessResult(BaseModel):
    """Schema for individual process result"""
    question: str = Field(..., description="The question text")
    answer: str = Field(..., description="The answer text")
    status: Literal["answer_found", "answer_notfound"] = Field(..., description="Status of the answer")

class ProcessResponse(BaseModel):
    """Schema for process response"""
    results: List[ProcessResult] = Field(..., description="List of processed results")
    count: int = Field(..., description="Number of results")
