"""渡劫飞升 · s5:PRD 总成——里程碑、验收与评审

把 s1-s4 的四块拼图(定位、架构、数据、接口)汇成一份完整 PRD,
补上里程碑计划与验收标准,渲染 docs/PRD.md 并做一次自动化评审。
"""
import os
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, Field

TAGLINE = "毕业设计 · 整合七章所学交付完整知识问答 Agent"


def md_table(headers: list, rows: list) -> str:
    lines = ["| " + " | ".join(headers) + " |"]
    lines += ["|" + "---|" * len(headers)] + ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(lines) + "\n"


# ---- 用户、故事与架构:浓缩为模块级数据 ----
USERS = [["入门散修", "快速搞懂基础功法"], ["金丹真人", "按状态定制突破方案"], ["宗门执事", "低门槛维护知识库"]]
STORIES = [["US-1", "作为入门散修,我想要检索基础功法,以便三天内入门"], ["US-2", "作为金丹真人,我想要对比突破心法,以便选出最适合的"], ["US-3", "作为宗门执事,我想要批量导入典籍,以便跟上藏经阁"]]
ARCH_COMPONENTS = {"web": "Web 界面", "api": "FastAPI 网关", "svc": "服务编排", "agent": "问答 Agent", "rag": "检索增强", "kb": "典籍库"}
LAYER_ORDER = [("展示层", ["web"]), ("接入层", ["api"]), ("业务层", ["svc", "agent", "rag"]), ("存储层", ["kb"])]
ARCH_EDGES = ["web --> api", "api --> svc", "svc --> agent", "agent --> rag", "rag --> kb"]


def render_mermaid() -> str:
    lines = ["flowchart TB"]
    for layer, comps in LAYER_ORDER:
        lines += [f"    subgraph {layer}"] + [f'        {c}["{ARCH_COMPONENTS[c]}"]' for c in comps] + ["    end"]
    return "\n".join(lines + ARCH_EDGES) + "\n"


# ---- 数据模型与接口契约:浓缩自 s3/s4 ----
class Document(BaseModel):
    doc_id: str
    title: str
    text: str


class RetrievalQuery(BaseModel):
    text: str = Field(min_length=2, description="用户提问")
    top_k: int = Field(default=5, gt=0, le=20)


class RetrievalHit(BaseModel):
    chunk_id: str
    score: float = Field(ge=0.0, le=1.0)


class EndpointSpec(BaseModel):
    method: Literal["GET", "POST"]
    path: str
    summary: str
    request_schema: Optional[dict] = None
    response_schema: dict


def endpoints() -> list:
    return [
        EndpointSpec(method="POST", path="/api/kb", summary="创建典籍库",
                     request_schema=Document.model_json_schema(), response_schema={"message": "ok"}),
        EndpointSpec(method="POST", path="/api/kb/documents", summary="导入典籍并切块",
                     request_schema=Document.model_json_schema(), response_schema={"doc_id": "kb-0001"}),
        EndpointSpec(method="POST", path="/api/retrieve", summary="检索典籍",
                     request_schema=RetrievalQuery.model_json_schema(), response_schema={"hits": [RetrievalHit.model_json_schema()]}),
        EndpointSpec(method="GET", path="/api/health", summary="健康检查",
                     request_schema=None, response_schema={"status": "ok"}),
    ]


def build_openapi(specs: list) -> dict:
    paths = {}
    for ep in specs:
        body = None if ep.request_schema is None else {"required": True, "content": {"application/json": {"schema": ep.request_schema}}}
        paths.setdefault(ep.path, {})[ep.method.lower()] = {"summary": ep.summary, "requestBody": body,
            "responses": {"200": {"description": "成功", "content": {"application/json": {"schema": ep.response_schema}}}}}
    return {"openapi": "3.0.3", "info": {"title": "渡劫飞升 API", "version": "0.1.0"}, "paths": paths}


# ---- 里程碑与验收 ----
def milestones() -> list:
    return [
        ["M1", "搭建检索管线", "FastAPI 服务 + Chroma 入库"],
        ["M2", "接入问答 Agent", "工具调用与多轮对话"],
        ["M3", "前端联调", "Web 界面跑通提问全流程"],
        ["M4", "部署与验收", "Docker Compose 一键上线"],
    ]


def acceptance_criteria() -> list:
    return [
        "AC-1:回答必须带出处与文档标题",
        "AC-2:top_k 越界请求返回 400,而非静默降级",
        "AC-3:单轮提问到回答耗时不超过 3 秒",
        "AC-4:至少 50 篇典籍入库,检索命中率不低于 80%",
        "AC-5:四套环境一键拉起,无手工配置",
    ]


def assemble_prd() -> str:
    doc = ["# 渡劫飞升 PRD", "", "> " + TAGLINE]
    doc.append("\n## 一、项目定位与用户故事\n")
    doc.append("- 一句话定位:" + TAGLINE)
    doc.append(md_table(["用户", "核心诉求"], USERS))
    doc.append(md_table(["编号", "故事"], STORIES))
    doc.append("\n## 二、系统架构\n")
    doc.append("```mermaid\n" + render_mermaid().rstrip() + "\n```")
    doc.append("\n## 三、数据模型\n")
    doc.append("Document:典籍原文;RetrievalQuery:检索请求;RetrievalHit:命中结果")
    doc.append("\n## 四、接口契约\n")
    doc.append("```yaml\n" + yaml.dump(build_openapi(endpoints()), allow_unicode=True, sort_keys=False).rstrip() + "\n```")
    doc.append("\n## 五、里程碑计划\n")
    doc.append(md_table(["编号", "目标", "产出"], milestones()))
    doc.append("\n## 六、验收标准\n")
    doc.append(md_table(["编号", "验收项"], [[c, "见" + c] for c in acceptance_criteria()]))
    return "\n".join(doc) + "\n"


def review_prd(text: str) -> list:
    sections = ["一、项目定位", "二、系统架构", "三、数据模型", "四、接口契约", "五、里程碑计划", "六、验收标准"]
    issues = ["缺少章节:" + s for s in sections if s not in text]
    issues += ["缺少要素:" + k for k in ["渡劫飞升", "RetrievalQuery", "mermaid", "openapi: 3.0.3"] if k not in text]
    if len(text) < 500:
        issues.append("正文过短,不足 500 字符")
    return issues


def main() -> None:
    os.makedirs("docs", exist_ok=True)
    text = assemble_prd()
    issues = review_prd(text)
    if not issues:
        issues = ["评审全部通过:六个章节齐备,要素完整"]
    for issue in issues:
        print(issue)
    with open("docs/PRD.md", "w", encoding="utf-8") as f:
        f.write(text)
    print(f"已写入 docs/PRD.md,正文共 {len(text)} 字符")


if __name__ == "__main__":
    main()
