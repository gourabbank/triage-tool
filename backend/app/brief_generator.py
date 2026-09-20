from .schemas import BriefSchema

def generate_mock_brief(raw_text: str) -> BriefSchema:
    return BriefSchema(
        problem_summary=f"Request appears to be about: {raw_text[:100]}",
        likely_users=["unspecified — needs clarification"],
        recommended_solution_type="needs_more_info",
        clarifying_questions=["Who is the requester?", "What does success look like?"],
        risks=["Underspecified request"],
        suggested_next_action="Schedule a scoping call.",
        model_used="mock-llm-v1",
    )