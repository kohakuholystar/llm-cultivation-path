# 黑糖资料室（毕业项目工作区）

这不是另一套示例代码。ch08 的 t70～t74 都在同一个 `capstone/` 目录上迭代：

1. t70 固定目录、配置、数据契约和 API 骨架，并让健康检查可测试；
2. t71 在 `app/rag.py` 实现 `KnowledgeBase.ingest()` 和 `KnowledgeBase.ask()`；
3. t72 在 `app/agent.py` 实现 Agent，并通过 `from app.rag import KnowledgeBase` 调用 RAG；
4. t73 将 `app/api.py` 封装为 FastAPI 服务，并补齐 Dockerfile、Compose；
5. t74 只运行这个项目的 pytest、API 冒烟与失败场景。

在本地工作区执行：

```powershell
cd capstone
python -m pytest
uvicorn app.api:app --reload
```

课程 IDE 目前一次只运行一个 Python 文件，不能替代多文件工程。每个 ch08 步骤都应在本目录对应文件中完成，并以本项目的测试为准；不要把后续模块复制回单文件练习。
