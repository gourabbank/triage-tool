import json
import os
from abc import ABC, abstractmethod
from .schemas import BriefSchema


class BaseBriefGenerator(ABC):
    @abstractmethod
    def generate(self, raw_text: str) -> BriefSchema:
        ...


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


class MockBriefGenerator(BaseBriefGenerator):
    def generate(self, raw_text: str) -> BriefSchema:
        return generate_mock_brief(raw_text)


PROMPT_TEMPLATE = """You are triaging an internal business request. Given the \
request below, return ONLY a JSON object (no markdown, no commentary) with \
exactly these keys:

- problem_summary: string, 1-2 sentences
- likely_users: array of strings
- recommended_solution_type: one of "internal_tool", "workflow_fix", "data_pull", "ai_agent", "needs_more_info"
- clarifying_questions: array of strings
- risks: array of strings
- suggested_next_action: string

Request:
\"\"\"{raw_text}\"\"\"
"""


class GroqBriefGenerator(BaseBriefGenerator):
    API_URL = "https://api.groq.com/openai/v1/chat/completions"
    MODEL = "openai/gpt-oss-20b"  # confirmed via GET /v1/models on this account

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is not set")

    def generate(self, raw_text: str) -> BriefSchema:
        import httpx
        response = httpx.post(
            self.API_URL,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={
                "model": self.MODEL,
                "messages": [{"role": "user", "content": PROMPT_TEMPLATE.format(raw_text=raw_text)}],
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
            },
            timeout=20.0,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Groq API error {response.status_code}: {response.text[:500]}")
        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return BriefSchema(**parsed, model_used=f"groq/{self.MODEL}")


class FallbackBriefGenerator(BaseBriefGenerator):
    def __init__(self, primary, fallback):
        self.primary = primary
        self.fallback = fallback

    def generate(self, raw_text: str) -> BriefSchema:
        try:
            return self.primary.generate(raw_text)
        except Exception:
            return self.fallback.generate(raw_text)


def get_generator() -> BaseBriefGenerator:
    if os.environ.get("GROQ_API_KEY"):
        return FallbackBriefGenerator(primary=GroqBriefGenerator(), fallback=MockBriefGenerator())
    return MockBriefGenerator()