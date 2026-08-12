/**
 * 课程树类型定义 —— 整个项目的核心数据契约。
 *
 * 层级: Course → Chapter[] → Task[] → Step[]
 * TS 为 single source of truth,后端 Pydantic 模型手工对齐(见 backend/app/models/course.py)。
 *
 * @see plan 第 2 节
 */

/** 课程根 */
export interface Course {
  id: string
  title: string
  description: string
  version: string // 语义化版本,用于进度迁移
  totalExp: number // 全课程可获总经验(计算用)
  chapters: Chapter[]
}

/** 章节解锁条件 */
export interface UnlockRequirement {
  requiredLevel: number // 达到该等级
  requiredExp: number // 达到该经验
  prerequisiteTaskIds: string[] // 需先完成的任务
}

/** 章节 */
export interface Chapter {
  id: string // 如 "ch01-llm-basics"
  courseId: string
  order: number
  title: string
  description: string
  theme: string // 剧情主题(如"初入江湖")
  unlock: UnlockRequirement
  tasks: Task[]
}

/** 任务难度 */
export type Difficulty = 'easy' | 'medium' | 'hard' | 'boss'

/** 任务(打怪单位) */
export interface Task {
  id: string // 如 "t01-first-call"
  chapterId: string
  order: number
  title: string
  scenario: string // 打怪剧情包装(markdown)
  learningGoal: string // 学完后能做什么
  difficulty: Difficulty
  expReward: number
  estimatedMinutes: number
  needsSandbox: boolean // 是否需要后端沙箱
  needsNetwork: boolean // 沙箱执行是否需要联网(调 LLM API 等)
  steps: Step[]
}

/** 步骤(最小学习+验证单元) */
export interface Step {
  id: string // 如 "t01-s1"
  taskId: string
  order: number
  title: string
  instruction: string // 本步骤说明(markdown)
  starterCode: string // 起始代码模板(含 # TODO: 注释占位)
  solutionCode: string // 参考答案
  hints: Hint[]
  todoItems: StepTodoItem[] // 任务清单(第 1 章试点): 每步可勾选的小任务
  codeSamples: CodeSample[]
  terms: Term[]
  techStack: TechStackItem[]
  validation: ValidationRule[] // 全部通过才算通关
  /** 真实框架最小示例的特例行数阈值；低于 40 时必须附说明。 */
  minimumSolutionLines?: number
  compactSolutionRationale?: string
  /** 是否需要真实网络运行；未设置时继承 task.needsNetwork。 */
  needsNetwork?: boolean
  /** 步骤级沙箱超时（秒）；仅用于明确标注的多轮真实调用，最高 120 秒。 */
  sandboxTimeout?: number
  /** 选择普通或模型课程沙箱；未设置时使用 core。 */
  sandboxProfile?: 'core' | 'ml'
}

export interface Hint {
  order: number // 揭示顺序
  text: string
}

/** 任务清单项(第 1 章试点, 课程 JSON 手写维护) */
export interface StepTodoItem {
  /** 做什么(一句话命令式, 从"### 操作"段提炼) */
  title: string
  /** 改哪里: 函数名 / 位置, 如 "APIConfig.from_env()" */
  target?: string
  /** 关键 API / 伪代码(渲染为代码块, 不剧透完整答案) */
  code?: string
  /** 完成后应看到的预期效果(怎么算做对了) */
  expect?: string
}

export interface CodeSample {
  title: string
  language: 'python' | 'bash' | 'text'
  code: string
  description?: string
}

export interface Term {
  name: string
  definition: string
  referenceUrl?: string
}

export interface TechStackItem {
  name: string // 如 "LangChain"
  role: string // 如 "Agent 编排框架"
  description: string
  officialUrl: string
  /** 技术分类(SDK/框架/工具/模型/库), 可选 */
  category?: string
  /** 安装提示(如 pip install xxx), 可选 */
  installHint?: string
}

/** 通关判定规则 —— discriminated union */
export type ValidationRule =
  | ApiCallExistsRule
  | PlaceholderFilledRule
  | RegexInCodeRule
  | OutputContainsRule
  | OutputMatchesRule
  | OutputEqualsRule
  | AstStructureRule
  | UnitTestRule
  | SandboxRunRule

/** 所有规则类型字面量 */
export type ValidationRuleType = ValidationRule['type']

export interface ValidationRuleBase {
  /** 规则简述,验证失败时展示给学习者 */
  message: string
  /** 该规则失败时是否阻断(默认 true);false 表示仅警告 */
  blocking?: boolean
}

export interface ApiCallExistsRule extends ValidationRuleBase {
  type: 'api_call_exists'
  /** 要检测的 API 调用,如 "openai.chat.completions.create" 或 "ChatOpenAI" */
  api: string
  /** 最少出现次数,默认 1 */
  minCount?: number
}

export interface PlaceholderFilledRule extends ValidationRuleBase {
  type: 'placeholder_filled'
  /** 占位符标记,如 "# TODO:" 或 "# YOUR CODE HERE" */
  placeholder: string
}

export interface RegexInCodeRule extends ValidationRuleBase {
  type: 'regex_in_code'
  pattern: string
  flags?: string // 如 'i' 'm'
}

export interface OutputContainsRule extends ValidationRuleBase {
  type: 'output_contains'
  text: string
  caseSensitive?: boolean // 默认 true
}

export interface OutputMatchesRule extends ValidationRuleBase {
  type: 'output_matches'
  pattern: string
  flags?: string
}

export interface OutputEqualsRule extends ValidationRuleBase {
  type: 'output_equals'
  expected: string
  trim?: boolean // 默认 true
  ignoreCase?: boolean // 默认 false
}

export interface AstStructureRule extends ValidationRuleBase {
  type: 'ast_structure'
  /** 检测的 AST 节点类型 */
  astType:
    | 'function_def'
    | 'async_function_def'
    | 'class_def'
    | 'import'
    | 'import_from'
    | 'call'
    | 'assign'
  /** 进一步匹配: 函数名/类名/导入模块/被调函数 */
  name?: string
  minCount?: number
}

export interface UnitTestRule extends ValidationRuleBase {
  type: 'unit_test'
  /** 测试代码(pytest 风格),与学习者代码合并后送沙箱跑 */
  testCode: string
}

export interface SandboxRunRule extends ValidationRuleBase {
  type: 'sandbox_run'
  /** 期望的 stdout(可叠加 output_* 规则进一步校验) */
  expectedStdout?: string
  /** stderr 必须为空 */
  stderrMustBeEmpty?: boolean
  /** 退出码 */
  expectedExitCode?: number
}

/** 沙箱执行输出(验证结果的一部分) */
export interface SandboxOutput {
  stdout: string
  stderr: string
  exitCode: number
  durationMs: number
  timedOut: boolean
}

/** 单条规则验证结果 */
export interface ValidationResult {
  ruleIndex: number
  ruleType: ValidationRuleType
  passed: boolean
  blocking?: boolean
  message: string
  details?: string
}

/** 步骤整体验证结果 */
export interface StepValidationResult {
  stepId: string
  allPassed: boolean
  results: ValidationResult[]
  sandboxOutput?: SandboxOutput
}
