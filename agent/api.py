from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List, Awaitable
from langgraph.types import Command
from .graph import workflow
from .models import InterviewState
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


DATABASE_URL = "./db/checkpoints.db"

api = FastAPI(title="AI agent-backend API")

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    # "https://your-production-frontend.com",
]

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

runnable_app = None
saver_instance: Optional[AsyncSqliteSaver] = None
saver_context_manager: Optional[Awaitable] = None


interview_sessions: Dict[str, str] = {}


class StartInterviewRequest(BaseModel):
    job_role: str
    candidate_id: str

class InterviewResponse(BaseModel):
    session_id: str # This will now be the generated UUID
    status: str
    current_question: Optional[Dict[str, Any]] = None
    feedback: Optional[str] = None
    overall_score: Optional[float] = None
    error_message: Optional[str] = None
    interview_history_summary: Optional[List[Dict[str, Any]]] = None


class SubmitAnswerRequest(BaseModel):
    candidate_response: str


@api.on_event("startup")
async def startup_event():
    global runnable_app, saver_instance, saver_context_manager
    try:
        saver_context_manager = AsyncSqliteSaver.from_conn_string("./db/checkpoints.db")
        saver_instance = await saver_context_manager.__aenter__()
        logger.info(f"AsyncSqliteSaver initialized with database: {DATABASE_URL}")
        runnable_app = workflow.compile(checkpointer=saver_instance)
        # logger.info(runnable_app.get_graph().draw_mermaid())
        logger.info("LangGraph workflow compiled with AsyncSqliteSaver.")

    except Exception as e:
        logger.error(f"Error during startup: Could not initialize saver or compile graph: {e}", exc_info=True) # Log exception details
        raise e


@api.on_event("shutdown")
async def shutdown_event():
    global saver_context_manager
    if saver_context_manager:
        await saver_context_manager.__aexit__(None, None, None)
        logger.info("AsyncSqliteSaver context exited.")


@api.post("/interview/start", response_model=InterviewResponse)
async def start_interview(request: StartInterviewRequest):
    global runnable_app
    if runnable_app is None:
        raise HTTPException(status_code=500,
                            detail="Graph not initialized. Server encountered a startup error.")

    generated_session_id = str(uuid.uuid4())
    interview_sessions[generated_session_id] = request.candidate_id
    logger.info(f"Generated session ID {generated_session_id} for candidate {request.candidate_id}")

    initial_state = InterviewState(
        job_role=request.job_role,
        candidate_id=generated_session_id
    )

    try:
        final_state = await runnable_app.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": generated_session_id}}
        )

        response_data = InterviewResponse(
            session_id=generated_session_id,
            status=final_state.get('interview_status', 'unknown'),
            current_question=final_state.get('current_question'),
            feedback=final_state.get('feedback'),
            overall_score=final_state.get('overall_score'),
            error_message=final_state.get('error_message'),
            interview_history_summary=final_state.get('interview_history_summary')
        )
        logger.info(f"Started interview session {generated_session_id} successfully.")
        return response_data

    except Exception as e:
        logger.error(f"Error starting interview for candidate {request.candidate_id} (session {generated_session_id}): {e}", exc_info=True)
        return InterviewResponse(
             session_id=generated_session_id,
             status='error',
             error_message=f"An internal error occurred while starting the interview: {e}"
        )


@api.post("/interview/{session_id}/submit_answer", response_model=InterviewResponse)
async def submit_answer(session_id: str, request: SubmitAnswerRequest):
    global runnable_app
    if runnable_app is None:
        raise HTTPException(status_code=500,
                            detail="Graph not initialized. Server encountered a startup error.")


    if session_id not in interview_sessions:
         logger.warning(f"Received submit for unknown session ID: {session_id}")
         raise HTTPException(status_code=404, detail=f"Interview session {session_id} not found or has expired.")

    logger.info(f"Received submit for session ID: {session_id}")


    try:

        final_state = await runnable_app.ainvoke(
            Command(resume=request.candidate_response),
            config={"configurable": {"thread_id": session_id}} # Use the UUID from the path
        )

        response_data = InterviewResponse(
            session_id=session_id,
            status=final_state.get('interview_status', 'unknown'),
            current_question=final_state.get('current_question'),
            feedback=final_state.get('feedback'),
            overall_score=final_state.get('overall_score'),
            error_message=final_state.get('error_message'),
            interview_history_summary=final_state.get('interview_history_summary')
        )
        logger.info(f"Processed answer for session {session_id}, status: {response_data.status}")
        return response_data

    except Exception as e:
        logger.error(f"Error submitting answer for session {session_id}: {e}", exc_info=True)
        return InterviewResponse(
             session_id=session_id,
             status='error',
             error_message=f"An error occurred while processing the answer: {e}"
        )


# uvicorn agent.api:api --reload