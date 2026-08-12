"""Trusted structural contract for the real CrewAI hierarchical exercise."""
from pathlib import Path


def test_uses_real_crewai_hierarchical_api() -> None:
    code = Path("student_submission.py").read_text(encoding="utf-8")
    assert "from crewai import Agent, Crew, LLM, Process, Task" in code
    assert "Process.hierarchical" in code
    assert "manager_llm=llm" in code
    assert "class Crew" not in code and "MOCK_LLM" not in code

