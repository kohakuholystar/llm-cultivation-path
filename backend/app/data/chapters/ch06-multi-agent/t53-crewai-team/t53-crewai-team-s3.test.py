"""Trusted structural contract for the real CrewAI sequential exercise.

CrewAI is intentionally not emulated in the sandbox test: execution requires the
learner's live DeepSeek key and a sandbox image containing the declared dependency.
"""
from pathlib import Path


def test_uses_real_crewai_sequential_api() -> None:
    code = Path("student_submission.py").read_text(encoding="utf-8")
    assert "from crewai import Agent, Crew, LLM, Process, Task" in code
    assert "Process.sequential" in code
    assert "Crew(" in code and "kickoff()" in code
    assert "OPENAI_API_KEY" in code and "MOCK_LLM" not in code

