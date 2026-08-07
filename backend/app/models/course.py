"""课程树 Pydantic 模型 —— 与 shared/types/course.ts 手工对齐。

约定: snake_case 字段 + alias_generator=to_camel,对外 JSON 用 camelCase。
TS 是 single source of truth,本文件字段与 shared/types/course.ts 一一对应。
"""
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """统一 camelCase 别名: Python 内 snake_case, 对外 JSON camelCase。"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )


class UnlockRequirement(CamelModel):
    required_level: int = 0
    required_exp: int = 0
    prerequisite_task_ids: list[str] = Field(default_factory=list)


class Hint(CamelModel):
    order: int
    text: str


class StepTodoItem(CamelModel):
    """任务清单项(第 1 章试点, 课程 JSON 手写维护)。"""

    title: str
    target: Optional[str] = None
    code: Optional[str] = None
    expect: Optional[str] = None


class CodeSample(CamelModel):
    title: str
    language: Literal["python", "bash", "text"] = "python"
    code: str
    description: Optional[str] = None


class Term(CamelModel):
    name: str
    definition: str
    reference_url: Optional[str] = None


class TechStackItem(CamelModel):
    name: str
    role: str = ""
    description: str = ""
    official_url: str = ""
    # 技术分类(SDK/框架/工具/模型/库), 可选
    category: str = ""
    # 安装提示(如 pip install xxx), 可选
    install_hint: str = ""


# --- Validation rules (discriminated union) ---
class _RuleBase(CamelModel):
    message: str
    blocking: bool = True


class ApiCallExistsRule(_RuleBase):
    type: Literal["api_call_exists"]
    api: str
    min_count: int = 1


class PlaceholderFilledRule(_RuleBase):
    type: Literal["placeholder_filled"]
    placeholder: str


class RegexInCodeRule(_RuleBase):
    type: Literal["regex_in_code"]
    pattern: str
    flags: Optional[str] = None


class OutputContainsRule(_RuleBase):
    type: Literal["output_contains"]
    text: str
    case_sensitive: bool = True


class OutputMatchesRule(_RuleBase):
    type: Literal["output_matches"]
    pattern: str
    flags: Optional[str] = None


class OutputEqualsRule(_RuleBase):
    type: Literal["output_equals"]
    expected: str
    trim: bool = True
    ignore_case: bool = False


class AstStructureRule(_RuleBase):
    type: Literal["ast_structure"]
    ast_type: Literal[
        "function_def",
        "async_function_def",
        "class_def",
        "import",
        "import_from",
        "call",
        "assign",
    ]
    name: Optional[str] = None
    min_count: int = 1


class UnitTestRule(_RuleBase):
    type: Literal["unit_test"]
    test_code: str


class SandboxRunRule(_RuleBase):
    type: Literal["sandbox_run"]
    expected_stdout: Optional[str] = None
    stderr_must_be_empty: bool = False
    expected_exit_code: Optional[int] = None


ValidationRule = Annotated[
    ApiCallExistsRule
    | PlaceholderFilledRule
    | RegexInCodeRule
    | OutputContainsRule
    | OutputMatchesRule
    | OutputEqualsRule
    | AstStructureRule
    | UnitTestRule
    | SandboxRunRule,
    Field(discriminator="type"),
]


class Step(CamelModel):
    id: str
    task_id: str
    order: int
    title: str
    instruction: str
    starter_code: str
    solution_code: str
    hints: list[Hint] = Field(default_factory=list)
    todo_items: list[StepTodoItem] = Field(default_factory=list)
    code_samples: list[CodeSample] = Field(default_factory=list)
    terms: list[Term] = Field(default_factory=list)
    tech_stack: list[TechStackItem] = Field(default_factory=list)
    validation: list[ValidationRule] = Field(default_factory=list)


class Task(CamelModel):
    id: str
    chapter_id: str
    order: int
    title: str
    scenario: str
    learning_goal: str
    difficulty: Literal["easy", "medium", "hard", "boss"]
    exp_reward: int
    estimated_minutes: int
    needs_sandbox: bool = False
    needs_network: bool = False
    steps: list[Step]


class Chapter(CamelModel):
    id: str
    course_id: str
    order: int
    title: str
    description: str
    theme: str
    unlock: UnlockRequirement
    tasks: list[Task]


class Course(CamelModel):
    id: str
    title: str
    description: str
    version: str
    total_exp: int
    chapters: list[Chapter]
