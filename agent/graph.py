
from langgraph.graph import StateGraph, END
from .models import InterviewState

from .nodes import (
    start_interview_node,
    select_question_node,
    ask_question_node,
    receive_response_node,
    process_response_node,
    generate_feedback_node,
    provide_feedback_node,
    update_state_node,
    decide_next_after_select,
    decide_next_after_update,
)
app = None
saver = None

workflow = StateGraph(InterviewState)
workflow.add_node("start_interview", start_interview_node)
workflow.add_node("select_question", select_question_node)
workflow.add_node("ask_question", ask_question_node)
workflow.add_node("receive_response", receive_response_node)
workflow.add_node("process_response", process_response_node)
workflow.add_node("generate_feedback", generate_feedback_node)
workflow.add_node("provide_feedback", provide_feedback_node)
workflow.add_node("update_state", update_state_node)



workflow.set_entry_point("start_interview")
workflow.add_edge("start_interview", "select_question")
workflow.add_conditional_edges(
    "select_question",
    decide_next_after_select,
    {
        "ask_question": "ask_question",
        END: END,
    }
)

workflow.add_edge("ask_question", "receive_response")
workflow.add_edge("receive_response", "process_response")
workflow.add_edge("process_response", "generate_feedback")
workflow.add_edge("generate_feedback", "provide_feedback")
workflow.add_edge("provide_feedback", "update_state")
workflow.add_conditional_edges(
    "update_state",
    decide_next_after_update,
    {
        "select_question": "select_question",
        END: END,
    }
)


