"""终期交付 · s1:PRD 骨架——项目定位与用户故事

毕业设计的第一块砖:用「项目定位 + 目标 + 用户故事」搭出 PRD 开篇,
让需求从一句口号变成可评审、可验收的条目。
"""


# === 学习契约（面向学生）===
# 本节目标：PRD 骨架:项目定位与用户故事。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `md_h2(text: str) -> str`：输入为签名中的参数；输出为 `str`。用途：渲染二级标题。
#   - `md_h3(text: str) -> str`：输入为签名中的参数；输出为 `str`。用途：渲染三级标题。
#   - `md_table(headers: list, rows: list) -> str`：输入为签名中的参数；输出为 `str`。用途：把二维数组渲染成 Markdown 表格。
#   - `target_users() -> list`：输入为签名中的参数；输出为 `list`。用途：返回目标用户表:[用户, 身份, 核心诉求]。
#   - `user_stories() -> list`：输入为签名中的参数；输出为 `list`。用途：返回用户故事表:[编号, 故事]。
#   - `build_prd_part1() -> str`：输入为签名中的参数；输出为 `str`。用途：渲染 PRD 第一章:项目定位 + 目标用户与用户故事。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
# 所属技术栈/模块：应用交付：RAG、Agent、FastAPI、Docker、pytest、性能与上线验收。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import os


# ---- 项目定位:一份 PRD 的开头三件套 ----
PROJECT = {
    "name": "黑糖资料室",
    "tagline": "毕业设计 · 整合七章所学交付完整知识问答 Agent",
    "background": "技术社区资料浩如烟海,自学者常因无人指点而状态失控。本项目打造一名问答 Agent:学习者提问,它检索项目组资料、必要时调用工具,并给出带出处的回答。",
}

# ---- 项目目标:可量化,才能验收 ----
GOALS = [
    "能对学习问题给出带出处的答案,答非所问率低于 5%",
    "从提问到出答案的平均耗时不超过 3 秒",
    "支持至少 50 篇资料入库,检索命中率不低于 80%",
]

# ---- 极简 Markdown 渲染器:PRD 全部由数据 + 渲染生成 ----
def md_h2(text: str) -> str:
    """渲染二级标题。"""
    return f"\n## {text}\n"


def md_h3(text: str) -> str:
    """渲染三级标题。"""
    return f"\n### {text}\n"


def md_table(headers: list, rows: list) -> str:
    """把二维数组渲染成 Markdown 表格。"""
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"


def target_users() -> list:
    """返回目标用户表:[用户, 身份, 核心诉求]。"""
    # TODO: 返回 3 行目标用户,每行 [用户, 身份, 核心诉求]
    # 提示: 覆盖三类角色——刚入门的新人、卡瓶颈的学习者、维护知识库的执事,
    #       诉求要具体可感知,如「快速搞懂基础方法,少走弯路」;return 二维列表
    raise NotImplementedError("t70-prd-architecture-s1 尚未实现:请按 TODO 提示补全 target_users")


def user_stories() -> list:
    """返回用户故事表:[编号, 故事]。"""
    # TODO: 返回 3 条用户故事,编号 US-1 到 US-3
    # 提示: 每条按「作为…,我想要…,以便…」句式书写,收益要落在句尾;
    #       return [[编号, 故事], ...]
    raise NotImplementedError("t70-prd-architecture-s1 尚未实现:请按 TODO 提示补全 user_stories")


def build_prd_part1() -> str:
    """渲染 PRD 第一章:项目定位 + 目标用户与用户故事。"""
    doc = ["# 黑糖资料室 PRD", "", "> 需求分析与系统设计文档(第一期)"]
    doc.append(md_h2("一、项目定位"))
    doc.append(f"- 项目名称:{PROJECT['name']}")
    doc.append(f"- 一句话定位:{PROJECT['tagline']}")
    doc.append(md_h3("背景"))
    doc.append(PROJECT["background"])
    doc.append(md_h3("目标"))
    for i, goal in enumerate(GOALS, 1):
        doc.append(f"{i}. {goal}")
    doc.append(md_h2("二、目标用户与用户故事"))
    doc.append(md_h3("目标用户"))
    doc.append(md_table(["用户", "身份", "核心诉求"], target_users()))
    doc.append(md_h3("用户故事"))
    doc.append(md_table(["编号", "故事"], user_stories()))
    return "\n".join(doc) + "\n"


def main() -> None:
    os.makedirs("docs", exist_ok=True)
    text = build_prd_part1()
    with open("docs/prd_part1.md", "w", encoding="utf-8") as f:
        f.write(text)
    print(f"黑糖资料室 PRD 骨架已写入 docs/prd_part1.md,正文共 {len(text)} 字符")


if __name__ == "__main__":
    main()
