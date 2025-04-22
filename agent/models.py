from typing import List, Dict, Any, Literal, Optional
from pydantic import BaseModel, Field
from .config import TOTAL_QUESTIONS_PLANNED
InterviewStatus = Literal['not_started', 'in_progress', 'completed', 'terminated']

class InterviewState(BaseModel):
    job_role: str
    candidate_id: str
    interview_history: List[Dict[str, Any]] = Field(default_factory=list)
    current_question: Optional[Dict[str, Any]] = None
    candidate_response: Optional[str] = None
    response_analysis: Optional[Dict[str, Any]] = None
    response_evaluation: Optional[Dict[str, Any]] = None
    feedback: Optional[str] = None
    overall_score: float = 0.0
    interview_status: InterviewStatus = 'not_started'
    questions_asked_count: int = 0
    total_questions_planned: int = TOTAL_QUESTIONS_PLANNED
    available_questions_pool: List[Dict[str, Any]] = Field(default_factory=list)
    interview_config: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True