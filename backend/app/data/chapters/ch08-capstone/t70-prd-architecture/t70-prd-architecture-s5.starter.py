"""终期交付 · s5:PRD 总成——里程碑、验收与评审

把 s1-s4 的四块拼图(定位、架构、数据、接口)汇成一份完整 PRD,
补上里程碑计划与验收标准,渲染 docs/PRD.md 并做一次自动化评审。
"""


# === 学习契约（面向学生）===
# 本节目标：PRD 总成:里程碑、验收与评审。完成后能把本节概念放入可运行的工程链路。
# 需要补写：acceptance_criteria；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `md_table(headers: list, rows: list) -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `render_mermaid() -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `endpoints() -> list`：输入为签名中的参数；输出为 `list`。用途：按本节调用链完成对应处理
#   - `build_openapi(specs: list) -> dict`：输入为签名中的参数；输出为 `dict`。用途：按本节调用链完成对应处理
#   - `milestones() -> list`：输入为签名中的参数；输出为 `list`。用途：按本节调用链完成对应处理
#   - `acceptance_criteria() -> list`：输入为签名中的参数；输出为 `list`。用途：按本节调用链完成对应处理
#   - `assemble_prd() -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `review_prd(text: str) -> list`：输入为签名中的参数；输出为 `list`。用途：按本节调用链完成对应处理
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `Document`：承载本节状态/数据；重点方法：见类定义。
#   - `RetrievalQuery`：承载本节状态/数据；重点方法：见类定义。
#   - `RetrievalHit`：承载本节状态/数据；重点方法：见类定义。
#   - `EndpointSpec`：承载本节状态/数据；重点方法：见类定义。
# 所属技术栈/模块：应用交付：RAG、Agent、FastAPI、Docker、pytest、性能与上线验收。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
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
USERS = [["入门自学者", "快速搞懂基础方法"], ["进阶用户", "按状态定制突破方案"], ["项目组执事", "低门槛维护知识库"]]
STORIES = [["US-1", "作为入门自学者,我想要检索基础方法,以便三天内入门"], ["US-2", "作为进阶用户,我想要对比突破方法,以便选出最适合的"], ["US-3", "作为项目组执事,我想要批量导入资料,以便跟上黑糖资料室"]]
ARCH_COMPONENTS = {"web": "Web 界面", "api": "FastAPI 网关", "svc": "服务编排", "agent": "问答 Agent", "rag": "检索增强", "kb": "知识库"}
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
        EndpointSpec(method="POST", path="/api/kb", summary="创建知识库",
                     request_schema=Document.model_json_schema(), response_schema={"message": "ok"}),
        EndpointSpec(method="POST", path="/api/kb/documents", summary="导入资料并切块",
                     request_schema=Document.model_json_schema(), response_schema={"doc_id": "kb-0001"}),
        EndpointSpec(method="POST", path="/api/retrieve", summary="检索资料",
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
    return {"openapi": "3.0.3", "info": {"title": "黑糖资料室 API", "version": "0.1.0"}, "paths": paths}


# ---- 里程碑与验收 ----
def milestones() -> list:
    # TODO: 补全 4 个里程碑 M1-M4,对应后续四个阶段
    # 提示: 每行 [编号, 目标, 产出],编号 M1-M4,分别对应搭建检索管线、
    #       接入问答 Agent、前端联调、部署验收;return 二维列表
    raise NotImplementedError("t70-prd-architecture-s5 尚未实现:请按 TODO 提示补全 milestones")


def acceptance_criteria() -> list:
    # TODO: 补全 5 条验收标准(AC-1 起)
    # 提示: 每条以「AC-N:」开头并写清可测项——回答带出处、top_k 越界返 400、
    #       单轮限时 3 秒、50 篇入库命中率 80%、四套环境一键拉起;
    #       return [字符串, ...]
    raise NotImplementedError("t70-prd-architecture-s5 尚未实现:请按 TODO 提示补全 acceptance_criteria")


def assemble_prd() -> str:
    doc = ["# 黑糖资料室 PRD", "", "> " + TAGLINE]
    doc.append("\n## 一、项目定位与用户故事\n")
    doc.append("- 一句话定位:" + TAGLINE)
    doc.append(md_table(["用户", "核心诉求"], USERS))
    doc.append(md_table(["编号", "故事"], STORIES))
    doc.append("\n## 二、系统架构\n")
    doc.append("```mermaid\n" + render_mermaid().rstrip() + "\n```")
    doc.append("\n## 三、数据模型\n")
    doc.append("Document:资料原文;RetrievalQuery:检索请求;RetrievalHit:命中结果")
    doc.append("\n## 四、接口契约\n")
    doc.append("```yaml\n" + yaml.dump(build_openapi(endpoints()), allow_unicode=True, sort_keys=False).rstrip() + "\n```")
    doc.append("\n## 五、里程碑计划\n")
    doc.append(md_table(["编号", "目标", "产出"], milestones()))
    doc.append("\n## 六、验收标准\n")
    # TODO: 用 acceptance_criteria() 渲染验收表并返回完整文档
    # 提示: 列头 ["编号", "验收项"],数据 [[c, "见" + c] for c in acceptance_criteria()],
    #       用 md_table 渲染后 append 进 doc;最后 return "\n".join(doc) + "\n"
    raise NotImplementedError("t70-prd-architecture-s5 尚未实现:请按 TODO 提示补全验收小节")


def review_prd(text: str) -> list:
    sections = ["一、项目定位", "二、系统架构", "三、数据模型", "四、接口契约", "五、里程碑计划", "六、验收标准"]
    issues = ["缺少章节:" + s for s in sections if s not in text]
    issues += ["缺少要素:" + k for k in ["黑糖资料室", "RetrievalQuery", "mermaid", "openapi: 3.0.3"] if k not in text]
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
