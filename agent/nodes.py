from typing import Dict, Any

from langgraph.types import interrupt

from .models import InterviewState
from langgraph.graph import END
from .database import fetch_questions_from_db
from .config import db
from datetime import datetime
from .llm_helpers import (
    call_llm_select_question,
    call_llm_analyze_and_evaluate_response,
    call_llm_generate_feedback,
)

def start_interview_node(state: InterviewState) -> Dict[str, Any]:
    print("--- Node: start_interview ---")
    job_role = state.job_role
    candidate_id = state.candidate_id

    print(f"Starting interview for {candidate_id} ({job_role})")

    questions_pool = fetch_questions_from_db(job_role)
    total_planned = min(len(questions_pool), state.total_questions_planned)
    updates = {
        "interview_status": "in_progress",
        "questions_asked_count": 0,
        "overall_score": 0.0,
        "interview_history": [],
        "available_questions_pool": questions_pool,
        "total_questions_planned": total_planned,
        "current_question": None,
        "candidate_response": None,
        "response_analysis": None,
        "response_evaluation": None,
        "feedback": None,
        "error_message": None,
    }

    return updates
def select_question_node(state: InterviewState) -> Dict[str, Any]:
    print("--- Node: select_question ---")
    available_questions = state.available_questions_pool
    asked_count = state.questions_asked_count
    total_planned = state.total_questions_planned
    interview_history = state.interview_history
    interview_config = state.interview_config
    job_role = state.job_role

    if asked_count >= total_planned:
         print("System limit reached: Reached planned questions count. Forcing end.")
         return {"interview_status": "completed"}



    llm_decision_result = call_llm_select_question(
        available_questions=available_questions,
        interview_history=interview_history,
        interview_config=interview_config,
        job_role=job_role,
    )

    error_message = None

    if llm_decision_result is None:
        print("LLM question selection failed or returned invalid result.")
        error_message = state.error_message or "Question selection failed."
        updates = {"interview_status": "terminated", "error_message": error_message}

    elif isinstance(llm_decision_result, dict) and llm_decision_result.get("action") == "end_interview":
         print("LLM decided to end the interview.")
         error_message = llm_decision_result.get('reason')
         updates = {"interview_status": "completed", "error_message": error_message or state.error_message}

    else:
        selected_question = llm_decision_result


        selected_id = selected_question.get('id')


        new_pool = [q for q in available_questions if q.get('id') != selected_id]

        print(f"Selected question from pool: ID {selected_id}")

        updates = {
            "current_question": selected_question,
            "available_questions_pool": new_pool,
            "interview_status": state.interview_status
        }


    if error_message is not None:
        updates["error_message"] = error_message

    return updates
def ask_question_node(state: InterviewState) -> Dict[str, Any]:
    print("--- Node: ask_question ---")
    question = state.current_question

    if question and question.get('text'):
        print(f"\nAI Interviewer asks: {question['text']}\n")

    else:
        print("Error: No current question found in state to ask.")
        return {"error_message": state.error_message or "No question available to ask."}


    return {}
def receive_response_node(state: InterviewState) -> Dict[str, Any]:
    candidate_response = interrupt(
        {
            "Question": state.current_question
        }
    )

    print("--- Node: receive_response ---")

    updates = {
        "candidate_response": candidate_response,
        "error_message": None,
    }
    return updates
def process_response_node(state: InterviewState) -> Dict[str, Any]:
    print("--- Node: process_response ---")
    question = state.current_question
    response = state.candidate_response
    job_role = state.job_role

    if not question or not response:
        print("Error: Missing question or response for processing.")
        error_msg = "Missing question or response for processing."
        return {"error_message": state.error_message or error_msg, "interview_status": "terminated"} # Terminate on critical error

    combined_result = call_llm_analyze_and_evaluate_response(question, response, job_role)

    updates = {}
    error_message = state.error_message

    if combined_result is None:
        print("Response analysis and evaluation failed.")
        error_message = error_message or "Response analysis and evaluation failed."
        updates = {"interview_status": "terminated"}
    else:
        print("Response analysis and evaluation successful.")
        updates = {
            "response_analysis": combined_result.get("analysis"),
            "response_evaluation": combined_result.get("evaluation"),
        }
        if combined_result.get("error_reason"):
             updates["error_message"] = combined_result["error_reason"]

    if error_message is not None:
        updates["error_message"] = error_message
    return updates
def generate_feedback_node(state: InterviewState) -> Dict[str, Any]:
    print("--- Node: generate_feedback ---")
    question = state.current_question
    response = state.candidate_response
    analysis = state.response_analysis
    evaluation = state.response_evaluation
    job_role = state.job_role


    if not question or not response or not analysis or not evaluation:
        print("Error: Missing data (Q, A, Analysis, or Evaluation) for feedback generation.")
        error_msg = "Missing data for feedback generation."
        return {"error_message": state.error_message or error_msg, "interview_status": "terminated"}

    feedback_text = call_llm_generate_feedback(
        question=question,
        response=response,
        analysis=analysis,
        evaluation=evaluation,
        job_role=job_role,
    )

    updates = {}
    error_message = state.error_message

    if feedback_text is None:
        print("Feedback generation failed.")
        error_message = error_message or "Feedback generation failed."
        updates = {"interview_status": "terminated"}
    else:
        print("Feedback generation successful.")
        updates = {"feedback": feedback_text}

    if error_message is not None:
        updates["error_message"] = error_message

    return updates
def provide_feedback_node(state: InterviewState) -> Dict[str, Any]:
    print("--- Node: provide_feedback ---")
    feedback = state.feedback

    if feedback:
        print(f"\nAI Interviewer provides feedback: {feedback}\n")
    else:
        print("Error: No feedback found in state to provide.")

        pass
    return {}


def update_state_node(state: InterviewState) -> Dict[str, Any]:
    print("--- Node: update_state ---")

    current_cycle_data = {
        "question": state.current_question,
        "response": state.candidate_response,
        "analysis": state.response_analysis,
        "evaluation": state.response_evaluation,
        "feedback": state.feedback,
        "timestamp": datetime.now()
    }

    interview_history = state.interview_history + [current_cycle_data]

    latest_score = state.response_evaluation.get("score", 0.0) if state.response_evaluation else 0.0
    if latest_score is  None:
        latest_score=0
    current_overall_score = state.overall_score + latest_score

    new_questions_asked_count = state.questions_asked_count + 1

    print(f"Cycle completed: Q {new_questions_asked_count}. Score for this Q: {latest_score:.2f}. Cumulative Score: {current_overall_score:.2f}")

    interview_status = state.interview_status
    if new_questions_asked_count >= state.total_questions_planned:
        print("Completion criteria met: Reached planned questions count.")
        interview_status = "completed"
    elif state.error_message:
         print(f"Error message found: {state.error_message}. Setting status to terminated.")
         interview_status = "terminated"


    updates = {
        "interview_history": interview_history,
        "overall_score": current_overall_score,
        "questions_asked_count": new_questions_asked_count,
        "interview_status": interview_status,
        "current_question": None,
        "candidate_response": None,
    }

    return updates

def decide_next_after_select(state: InterviewState):

    print("--- Router: decide_next_after_select ---")
    if state.interview_status in ['completed', 'terminated']:
        print(f"Interview status is {state.interview_status}. Ending.")
        return END
    elif state.current_question:
        print("Question selected. Proceeding to ask_question.")
        return "ask_question"
    else:
        print("No question selected and status not terminal. Forcing termination.")
        return END

def decide_next_after_update(state: InterviewState):

    print("--- Router: decide_next_after_update ---")
    if state.interview_status in ['completed', 'terminated']:
        print(f"Interview status is {state.interview_status}. Ending.")
        return END
    elif state.questions_asked_count < state.total_questions_planned and state.available_questions_pool:
        print(f"Asked {state.questions_asked_count}/{state.total_questions_planned} questions. Questions left: {len(state.available_questions_pool)}. Proceeding to select next question.")
        return "select_question"
    else:
        print("Completion criteria met or no questions left. Ending interview.")
        return END

