from typing import List, Dict, Any, Optional
import json
from .config import llm


def call_llm_select_question(
        available_questions: List[Dict[str, Any]],
        interview_history: List[Dict[str, Any]],
        interview_config: Dict[str, Any],
        job_role: str,
) -> Dict[str, Any] | None:
    print("Loading next question...")

    history_summary = []
    for i, turn in enumerate(interview_history[-3:]):
        history_summary.append(f"Turn {len(interview_history) - len(interview_history[-3:]) + i + 1}:")
        if turn.get('question'):
            history_summary.append(f"Q: {turn['question'].get('text', 'N/A')}")
        if turn.get('response'):
            history_summary.append(f"A: {turn['response'][:150]}...")
        if turn.get('evaluation'):
            eval_details = turn['evaluation']
            history_summary.append(
                f"Eval: Score={eval_details.get('score')}, Relevance={eval_details.get('relevance')}")
        if turn.get('feedback'):
            history_summary.append(f"Feedback Points: {turn['feedback'][:100]}...")

    available_q_list = []
    for q in available_questions:
        if q.get('id') and q.get('text'):
            available_q_list.append(
                f"- ID: {q.get('id')}, Topic: {q.get('topic', 'N/A')}, Difficulty: {q.get('difficulty', 'N/A')}, Text: {q.get('text', '')[:100]}...")

    prompt_text = f"""
    You are an AI interviewer conducting an interview for a {job_role} role.
    Your goal is to select the best next question from the provided list or determine if the interview should end.

    Interview Context:
    - Job Role: {job_role}
    - Interview Configuration: {json.dumps(interview_config)}
    - Recent Interview History:
    {'-' * 20}
    {'\n'.join(history_summary) if history_summary else 'No history yet.'}
    {'-' * 20}

    Available Questions in Pool ({len(available_questions)} questions):
    {'\n'.join(available_q_list) if available_q_list else 'No questions left in pool.'}

    Instructions:
    1. Review the interview history to understand what has been covered and the candidate's performance (especially the most recent turn).
    2. Review the available questions, considering their topic and difficulty.
    3. Choose ONE best question from the "Available Questions in Pool" list to ask next. Prioritize covering diverse topics relevant to the job role, potentially adjusting difficulty based on performance. Consider asking follow-up style questions from the pool if the last answer was insufficient on a specific point related to an available question.
    4. If the available pool is empty OR if based on the history and remaining questions you determine the interview should logically conclude (e.g., all key areas covered, candidate performance is clear, candidate seems struggling/expert), indicate that the interview should end. The primary end condition check (total planned questions reached) is handled by the main graph, but the LLM can suggest ending early.
    5. Respond ONLY with a valid JSON object.
    6. If you select a question, the JSON must have the key "selected_question_id" with the exact string ID from the "Available Questions in Pool" list.
    7. If you decide to end, the JSON must have the key "action" with the value "end_interview" and optionally a "reason" key.

    JSON Response Format Examples:
    {{ "action": "ask_question", "selected_question_id": "q5_se" }}
    {{ "action": "end_interview", "reason": "Candidate performance is clear." }}

    Ensure your response contains ONLY the JSON object and is valid. Do not add any other text before or after the JSON. Also ensure the each JSON object should contain an "action".
    """

    print(f"Sending prompt ({len(prompt_text)} chars) to LLM...")
    response_content = None
    try:
        llm_response = llm.invoke(prompt_text, {"recursion_limit": 100})
        response_content = llm_response.content
        print(f"LLM Raw Response received.")
    except Exception as e:
        print(f"LLM call failed: {e}")
        return None

    if not response_content:
        print("LLM response was empty.")
        return None

    response_content = response_content.strip()
    if response_content.startswith("```json"):
        response_content = response_content[len("```json"):].strip()
        if response_content.endswith("```"):
            response_content = response_content[:-len("```")].strip()

    llm_decision = None
    try:
        llm_decision = json.loads(response_content)
        print(f"Parsed LLM Decision: {llm_decision}")
    except json.JSONDecodeError:
        print(f"Failed to parse LLM response as JSON: {response_content}")
        return None

    if not isinstance(llm_decision, dict):
        print(f"Parsed LLM response is not a dictionary: {llm_decision}")
        return None

    action = llm_decision.get("action")

    if action == "ask_question":
        selected_id = llm_decision.get("selected_question_id")
        if selected_id:
            selected_question = next((q for q in available_questions if q.get('id') == selected_id), None)
            if selected_question:
                print(f"LLM selected question ID: {selected_id}")
                return selected_question
            else:
                print(f"LLM selected ID '{selected_id}' not found in available pool.")
                return None

        else:
            print("LLM action was 'ask_question' but no 'selected_question_id' provided.")
            return None

    elif action == "end_interview":
        print(f"LLM decided to end interview. Reason: {llm_decision.get('reason', 'N/A')}")
        return {"action": "end_interview", "reason": llm_decision.get('reason')}

    else:
        print(f"LLM returned unknown action: {action}")
        return None


def call_llm_analyze_and_evaluate_response(
        question: Dict[str, Any],
        response: str,
        job_role: str,
) -> Dict[str, Any] | None:
    print(f"-> LLM: Calling Gemini for combined analysis & evaluation...")

    prompt_text = f"""
    You are an AI interviewer evaluating a candidate's response for a {job_role} role.

    Question Asked: {question.get('text', 'N/A')}
    Candidate Response: {response}

    Instructions:
    Analyze the candidate's response thoroughly based on the question asked and the context of a {job_role} role.
    Then, evaluate the response quality and assign a score.
    Respond ONLY with a valid JSON object containing both analysis and evaluation details.

    JSON Response Format:
    {{
      "analysis": {{
        "key_points_extracted": [], // List of main ideas/facts mentioned
        "relevance_to_question": "", // How well the response addresses the question ("high" | "medium" | "low" | "partial")
        "clarity_assessment": "", // How easy the response was to understand ("clear" | "somewhat clear" | "unclear")
        "technical_accuracy_assessment": "", // If applicable, assess technical correctness ("accurate" | "mostly accurate" | "some inaccuracies" | "inaccurate" | "not applicable")
        "confidence_level": "", // Based on language used ("high" | "medium" | "low")
        "sentiment": "", // ("positive" | "neutral" | "negative")
        "keywords": [] // Relevant terms mentioned
        // Add other analysis points relevant to job role
      }},
      "evaluation": {{
        "score": null, // Assign a score (int out of 10). Use null if not scorable.
        "overall_evaluation_summary": "", // Concise summary of the evaluation for this response
        "relevance_judgment": "", // ("Relevant" | "Partially Relevant" | "Not Relevant")
        "strengths": [], // Key positive points
        "areas_for_improvement": [] // Key points to improve or points missed
        // Add other evaluation points specific to question/role
      }}
    }}

    Ensure your response contains ONLY the JSON object and is valid. Do not add any other text.
    Fill all keys in the JSON object based on the response. Use null or empty arrays/strings where information is not applicable or found.
    """

    print(f"Sending combined analysis/evaluation prompt ({len(prompt_text)} chars) to LLM...")
    response_content = None

    try:
        llm_response = llm.invoke(prompt_text, {"recursion_limit": 100})
        response_content = llm_response.content
        print("LLM Raw Response for combined analysis/evaluation received.")
    except Exception as e:
        print(f"LLM combined analysis/evaluation call failed: {e}")
        return None

    if not response_content:
        print("LLM combined analysis/evaluation response was empty.")
        return None

    response_content = response_content.strip()
    if response_content.startswith("```json"):
        response_content = response_content[len("```json"):].strip()
        if response_content.endswith("```"):
            response_content = response_content[:-len("```")].strip()

    combined_result = None
    try:
        combined_result = json.loads(response_content)
        print("Parsed LLM Combined Result.")
        if (
                not isinstance(combined_result, dict) or
                "analysis" not in combined_result or
                "evaluation" not in combined_result or
                not isinstance(combined_result.get("evaluation"), dict) or
                "score" not in combined_result["evaluation"]
        ):
            print("Parsed combined result is not a valid structure or missing score.")
            return None

        score = combined_result["evaluation"].get("score")
        if score is not None and not isinstance(score, (int, float)):
            try:
                combined_result["evaluation"]["score"] = float(score)
            except (ValueError, TypeError):
                print(f"Evaluation score is not a valid number: {score}")
                return None


    except json.JSONDecodeError:
        print(f"Failed to parse LLM combined analysis/evaluation response as JSON: {response_content}")
        return None

    return combined_result


def call_llm_generate_feedback(
        question: Dict[str, Any],
        response: str,
        analysis: Dict[str, Any],
        evaluation: Dict[str, Any],
        job_role: str,
) -> str | None:
    print(f"-> LLM: Calling Gemini for feedback generation...")


    prompt_text = f"""
    You are an AI interviewer providing feedback on a candidate's response for a {job_role} role.
    You have analyzed and evaluated their response.

    Question Asked: {question.get('text', 'N/A')}
    Candidate Response: {response[:200]}... # Provide snippet of raw response for context
    Analysis Results: {json.dumps(analysis, indent=2)[:500]}... # Provide snippet of analysis
    Evaluation Results: {json.dumps(evaluation, indent=2)[:500]}... # Provide snippet of evaluation (includes score, strengths, improvements)

    Instructions:
    1. Generate clear, constructive, and encouraging feedback for the candidate regarding their response to the question.
    2. Base the feedback on the provided Analysis and Evaluation results, specifically mentioning strengths and areas for improvement identified in the evaluation.
    3. Include the score for this specific response (from Evaluation Results) in the feedback.
    4. Keep the feedback concise and directly related to the response provided.
    5. Address the candidate directly (e.g., "Your response regarding...").
    6. Avoid conversational filler outside the direct feedback role.

    Provide ONLY the feedback text as a plain string. Do not include JSON or any other formatting unless explicitly part of the feedback content.
    """

    print(f"Sending feedback prompt ({len(prompt_text)} chars) to LLM...")
    response_content = None
    try:
        llm_response = llm.invoke(prompt_text, {"recursion_limit": 100})
        response_content = llm_response.content
        print("LLM Raw Response for feedback received.")
    except Exception as e:
        print(f"LLM feedback generation call failed: {e}")
        return None

    if not response_content:
        print("LLM feedback response was empty.")
        return None

    feedback_text = response_content.strip()

    print(f"Generated feedback (first 50 chars): {feedback_text[:50]}...")

    return feedback_text


