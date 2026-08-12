"""Trusted structural contract for the CrewAI project closing exercise."""
from pathlib import Path


def test_crewai_result_is_persisted() -> None:
    code = Path("student_submission.py").read_text(encoding="utf-8")
    assert "from crewai import Agent, Crew, LLM, Process, Task" in code
    assert "Process.sequential" in code and "kickoff()" in code
    assert "result.raw" in code and "encoding=\"utf-8\"" in code
    assert "OPENAI_API_KEY" in code and "MOCK_LLM" not in code
