"""渡劫飞升 · s2:系统架构——mermaid 架构图分层

把系统按展示、接入、业务、能力、存储五层切分,
组件间的连线即数据流,自上而下、不可反向。
"""
import os

TAGLINE = "毕业设计 · 整合七章所学交付完整知识问答 Agent"


def md_table(headers: list, rows: list) -> str:
    """把二维数组渲染成 Markdown 表格。"""
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"


# ---- 架构分层:自上而下五层 ----
LAYER_ORDER = [
    ("展示层", ["web"]),
    ("接入层", ["api"]),
    ("业务层", ["svc", "agent", "rag"]),
    ("能力层", ["harness", "vec"]),
    ("存储层", ["kb", "mem"]),
]

# ---- 组件清单:名字 -> 职责说明 ----
ARCH_COMPONENTS = {
    "web": "Web 界面:修行者提问与阅读回答的入口",
    "api": "FastAPI 网关:统一接收请求、做鉴权与限流",
    "svc": "服务编排:串联检索、Agent 决策与回答组装",
    "agent": "问答 Agent:规划、调用工具、管理多轮上下文",
    "rag": "检索增强:典籍切块、向量化、相关性召回",
    "harness": "工具执行:在安全沙箱里运行外部工具",
    "vec": "向量服务:相似度检索与重排",
    "kb": "典籍库:功法原文与切块(文档+向量)",
    "mem": "记忆库:多轮会话上下文与用户画像",
}

# ---- 技术选型:组件与技术的映射 ----
TECH_STACK = [
    ["层", "技术", "用途"],
    ["前端", "Vue 3", "问答界面"],
    ["接入", "FastAPI + uvicorn", "网关与服务进程"],
    ["业务", "LangChain", "Agent 编排"],
    ["模型", "DeepSeek deepseek-v4-pro", "对话与工具决策"],
    ["存储", "Chroma + SQLite", "向量库与元数据"],
    ["部署", "Docker Compose", "一键拉起全部服务"],
]


def arch_edges() -> list:
    """返回架构图连线:每条形如 'a --> b'。"""
    # TODO: 补全 8 条连线,串起 展示→接入→业务→能力→存储 的数据流
    # 提示: web→api→svc→agent 一路向下,再从 agent 分出 rag/harness/mem,
    #       rag 再连 vec 与 kb;每条形如 "a --> b",可给主干线加 |文字| 标注;
    #       return [字符串, ...]
    raise NotImplementedError("t70-prd-architecture-s2 尚未实现:请按 TODO 提示补全 arch_edges")


def render_mermaid() -> str:
    """用 subgraph 分层渲染 flowchart,组件放在对应层内。"""
    parts = ["flowchart TB"]
    for layer, comps in LAYER_ORDER:
        parts.append(f"    subgraph {layer}")
        for c in comps:
            parts.append(f'        {c}["{ARCH_COMPONENTS[c]}"]')
        parts.append("    end")
    for edge in arch_edges():
        parts.append(f"    {edge}")
    return "\n".join(parts) + "\n"


def check_diagram(text: str) -> None:
    """体检生成的 mermaid:连线、分组、闭合数量全部对上。"""
    # TODO: 统计连线、分组、闭合数量并逐一断言
    # 提示: edges = text.count("-->");groups = text.count("subgraph");
    #       ends = text.count("end");断言 edges >= 8、groups == len(LAYER_ORDER)、
    #       ends == groups;最后打印 f"校验通过:共 {edges} 条连线、{groups} 个分组,层次闭合"
    raise NotImplementedError("t70-prd-architecture-s2 尚未实现:请按 TODO 提示补全 check_diagram")


def main() -> None:
    os.makedirs("docs", exist_ok=True)
    diagram = render_mermaid()
    check_diagram(diagram)
    doc = ["# 渡劫飞升 · 系统架构", "", "> " + TAGLINE]
    doc.append("```mermaid")
    doc.append(diagram)
    doc.append("```")
    doc.append("## 技术选型")
    doc.append(md_table(TECH_STACK[0], TECH_STACK[1:]))
    with open("docs/architecture.mmd", "w", encoding="utf-8") as f:
        f.write("\n".join(doc) + "\n")
    print(f"已写入 docs/architecture.mmd,共 {len(diagram.splitlines())} 行 mermaid")


if __name__ == "__main__":
    main()
