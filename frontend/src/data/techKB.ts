/**
 * 技术知识库 —— 供 /docs 页面 TechReference 组件渲染。
 *
 * 按主题分组, 每个技术含: 分类/介绍/API要点/安装/官方文档。
 * "用到的地方"由 TechReference 组件从 course API 动态聚合(扫描所有 step.techStack)。
 */

export interface TechInfo {
  /** 规范技术名(展示用) */
  name: string
  /** 匹配 key(归一化小写, 用于和课程 techStack.name 匹配) */
  matchKeys: string[]
  category: string
  description: string
  apiPoints: string
  installHint: string
  officialUrl: string
}

export interface TechGroup {
  title: string
  icon: string
  techs: TechInfo[]
}

export const TECH_GROUPS: TechGroup[] = [
  {
    title: 'LLM SDK 与模型调用',
    icon: '🔌',
    techs: [
      {
        name: 'openai',
        matchKeys: ['openai', 'openai python sdk'],
        category: 'LLM SDK',
        description:
          'OpenAI 官方 Python SDK,是与大模型对话的核心入口。提供 chat.completions.create 调用对话模型,支持流式输出、函数调用(Tool Calls)、JSON 结构化输出、多轮对话上下文。' +
          '通过 base_url 参数可切换到 DeepSeek/通义/Moonshot 等国内兼容接口——同一套代码,只改 base_url 和 model,就能调用不同厂商的模型,是国内开发者最常用的 SDK。' +
          '本课程所有 LLM 调用都基于它,是入门第一步。',
        apiPoints:
          'from openai import OpenAI\n' +
          '\n' +
          '# 创建客户端(base_url 决定调哪个厂商)\n' +
          'client = OpenAI(\n' +
          '    api_key=os.environ["OPENAI_API_KEY"],\n' +
          '    base_url="https://api.deepseek.com",\n' +
          ')\n' +
          '\n' +
          '# 单次对话\n' +
          'response = client.chat.completions.create(\n' +
          '    model="deepseek-v4-pro",\n' +
          '    messages=[{"role": "user", "content": "你好"}],\n' +
          ')\n' +
          'print(response.choices[0].message.content)\n' +
          '\n' +
          '# 流式输出(stream=True 遍历响应)\n' +
          'for chunk in client.chat.completions.create(\n' +
          '    model="deepseek-v4-pro", messages=[...], stream=True\n' +
          '):\n' +
          '    print(chunk.choices[0].delta.content, end="")\n' +
          '\n' +
          '# JSON 结构化输出\n' +
          'response_format={"type": "json_object"}',
        installHint: 'pip install openai',
        officialUrl: 'https://pypi.org/project/openai/',
      },
      {
        name: 'DeepSeek',
        matchKeys: ['deepseek', 'deepseek api', 'deepseek-v4-pro', 'deepseek v4 pro'],
        category: '模型服务',
        description:
          'DeepSeek 是国产开源大模型厂商,提供 OpenAI 兼容 API(base_url=https://api.deepseek.com),价格远低于 OpenAI。' +
          '本项目默认使用 deepseek-v4-pro 模型:课程所有示例、全局 AI 配置、沙箱验证都基于它。' +
          '通过改 base_url 即可无缝切换其他 OpenAI 兼容服务(通义/Moonshot 等),是学习 LLM 开发最划算的选择。',
        apiPoints:
          'from openai import OpenAI\n' +
          '\n' +
          '# 关键: base_url 指向 DeepSeek\n' +
          'client = OpenAI(\n' +
          '    api_key=os.environ["OPENAI_API_KEY"],\n' +
          '    base_url="https://api.deepseek.com",\n' +
          ')\n' +
          '\n' +
          'resp = client.chat.completions.create(\n' +
          '    model="deepseek-v4-pro",\n' +
          '    messages=[{"role": "user", "content": "你好"}],\n' +
          ')\n' +
          'print(resp.choices[0].message.content)',
        installHint: 'pip install openai',
        officialUrl: 'https://platform.deepseek.com/',
      },
    ],
  },
  {
    title: 'LLM 应用框架',
    icon: '🧩',
    techs: [
      {
        name: 'LangChain',
        matchKeys: ['langchain'],
        category: 'LLM 框架',
        description:
          'LangChain 是构建 LLM 应用的主流框架,提供链式调用(Chain)、记忆(Memory)、工具(Tool)、Agent 编排、输出解析器等核心抽象。' +
          '它的核心思想是把 LLM 调用拆解成可组合的"组件"(模型、提示词、解析器、工具),用链(Chain)串联成复杂应用。' +
          '相比直接调 SDK,LangChain 让你专注业务逻辑而非底层调用细节,是 LLM 应用开发的事实标准。',
        apiPoints:
          '# 链式调用: 模型 | 提示词 | 解析器 串联\n' +
          'from langchain_openai import ChatOpenAI\n' +
          'from langchain_core.prompts import ChatPromptTemplate\n' +
          '\n' +
          'llm = ChatOpenAI(model="deepseek-v4-pro")\n' +
          'prompt = ChatPromptTemplate.from_template("{question}")\n' +
          'chain = prompt | llm\n' +
          'result = chain.invoke({"question": "什么是LangChain"})\n' +
          '\n' +
          '# 三种调用方式\n' +
          'llm.invoke(messages)   # 单次\n' +
          'llm.batch([m1, m2])    # 批量(并发)\n' +
          'llm.stream(messages)   # 流式\n' +
          '\n' +
          '# 定义工具(@tool 装饰器)\n' +
          '@tool\n' +
          'def get_time(city: str) -> str:\n' +
          '    """获取时间"""\n' +
          '    return "12:00"',
        installHint: 'pip install langchain',
        officialUrl: 'https://www.langchain.com/',
      },
      {
        name: 'langchain-openai',
        matchKeys: ['langchain-openai', 'langchain_openai', 'langchain openai'],
        category: '集成包',
        description:
          'LangChain 的 OpenAI 集成包,提供 ChatOpenAI 类封装对话模型,把原生 SDK 调用包装成 LangChain 的 Runnable 接口。' +
          '支持同步/异步/流式/批量调用,自动处理消息格式转换与重试,是 LangChain 链式调用的基础组件。' +
          '同样可通过 base_url 兼容国内模型(DeepSeek 等)。',
        apiPoints:
          'from langchain_openai import ChatOpenAI\n' +
          'from langchain_core.messages import HumanMessage\n' +
          '\n' +
          'llm = ChatOpenAI(\n' +
          '    model="deepseek-v4-pro",\n' +
          '    base_url="https://api.deepseek.com",\n' +
          '    api_key=os.environ["OPENAI_API_KEY"],\n' +
          ')\n' +
          '\n' +
          'messages = [HumanMessage(content="你好")]\n' +
          'response = llm.invoke(messages)\n' +
          'print(response.content)',
        installHint: 'pip install langchain-openai',
        officialUrl: 'https://python.langchain.com/docs/integrations/llms/openai/',
      },
      {
        name: 'langchain-core',
        matchKeys: ['langchain-core'],
        category: '核心库',
        description:
          'LangChain 核心抽象库,定义 Runnable 接口、消息类型(HumanMessage/AIMessage/SystemMessage)、输出解析器、文档加载器基础等。' +
          'Runnable 是 LangChain 的统一抽象——模型/提示词/解析器/工具都实现它,可自由组合。' +
          '所有 LangChain 包都依赖它,是理解 LangChain 架构的基础。',
        apiPoints:
          '# Runnable 接口(统一抽象)\n' +
          'from langchain_core.runnables import Runnable\n' +
          '\n' +
          '# 消息类型\n' +
          'from langchain_core.messages import (\n' +
          '    HumanMessage, AIMessage, SystemMessage\n' +
          ')\n' +
          '\n' +
          '# 输出解析器\n' +
          'from langchain_core.output_parsers import (\n' +
          '    StrOutputParser, JsonOutputParser\n' +
          ')\n' +
          '\n' +
          'chain = prompt | llm | StrOutputParser()',
        installHint: 'pip install langchain-core',
        officialUrl: 'https://python.langchain.com/docs/modules/core/',
      },
      {
        name: 'langchain-text-splitters',
        matchKeys: ['langchain-text-splitters', 'langchain_text_splitters', 'langchain text splitters'],
        category: '文本切分',
        description:
          'LangChain 官方文本切分包,把长文档切成适合 Embedding/检索的小块(chunk)。' +
          '核心是 RecursiveCharacterTextSplitter:按换行/句号/字符逐级递归切分,尽量保持语义完整,同时用 chunk_size/chunk_overlap 控制长度与重叠。' +
          'RAG 知识库构建的第一步——切分质量直接影响后续检索效果。',
        apiPoints:
          'from langchain_text_splitters import (\n' +
          '    RecursiveCharacterTextSplitter,\n' +
          ')\n' +
          '\n' +
          '# 按字符递归切分(默认分隔符: 换行→句号→字符)\n' +
          'splitter = RecursiveCharacterTextSplitter(\n' +
          '    chunk_size=200,      # 每块约 200 字符\n' +
          '    chunk_overlap=50,    # 块间重叠 50 字符(防断句丢信息)\n' +
          ')\n' +
          '\n' +
          '# 切分文档\n' +
          'chunks = splitter.split_text(long_text)\n' +
          '# chunks = splitter.split_documents(docs)  # 切 Document 对象(带 metadata)',
        installHint: 'pip install langchain-text-splitters',
        officialUrl: 'https://python.langchain.com/docs/how_to/recursive_text_splitter/',
      },
      {
        name: 'LangGraph',
        matchKeys: ['langgraph'],
        category: 'Agent 框架',
        description:
          'LangGraph 是 LangChain 推出的有状态多 Agent 编排框架,基于图结构定义节点(Node)与边(Edge)。' +
          '支持循环、条件分支、人机协作、持久化状态,比 AgentExecutor 更灵活强大,适合复杂 Agent 工作流。' +
          '多 Agent 协作、有状态的对话流程、需要回溯/分支的场景都用它。',
        apiPoints:
          'from langgraph.graph import StateGraph\n' +
          '\n' +
          '# 定义状态图\n' +
          'graph = StateGraph(StateSchema)\n' +
          'graph.add_node("agent", agent_fn)\n' +
          'graph.add_node("tool", tool_fn)\n' +
          '\n' +
          '# 加边(顺序/条件)\n' +
          'graph.add_edge("agent", "tool")\n' +
          'graph.add_conditional_edges("agent", route_fn)\n' +
          '\n' +
          '# 编译后调用\n' +
          'app = graph.compile()\n' +
          'app.invoke({"input": "..."})',
        installHint: 'pip install langgraph',
        officialUrl: 'https://langchain-ai.github.io/langgraph/',
      },
    ],
  },
  {
    title: '向量检索与 RAG',
    icon: '🔍',
    techs: [
      {
        name: 'sentence-transformers',
        matchKeys: ['sentence-transformers', 'sentence_transformers'],
        category: '嵌入模型',
        description:
          '提供多种预训练句子嵌入模型(如 all-MiniLM-L6-v2),把文本转成固定维度数值向量,使语义相似的文本向量距离更近。' +
          '本地运行无需 API 调用,适合语义搜索、文本聚类、RAG 检索增强等场景。是本地 RAG 的核心组件。',
        apiPoints:
          'from sentence_transformers import SentenceTransformer\n' +
          '\n' +
          "model = SentenceTransformer('all-MiniLM-L6-v2')\n" +
          '\n' +
          '# 文本转向量(384 维)\n' +
          'embedding = model.encode("机器学习是AI的一个分支")\n' +
          'print(len(embedding))  # 384\n' +
          '\n' +
          '# 批量编码\n' +
          'vectors = model.encode(["句子1", "句子2"])\n' +
          '\n' +
          '# 余弦相似度\n' +
          'from sklearn.metrics.pairwise import cosine_similarity\n' +
          'sim = cosine_similarity([vectors[0]], [vectors[1]])',
        installHint: 'pip install sentence-transformers',
        officialUrl: 'https://www.sbert.net/',
      },
      {
        name: 'ChromaDB',
        matchKeys: ['chromadb'],
        category: '向量数据库',
        description:
          'Chroma 是开源的本地向量数据库,支持存储文档+嵌入向量并做相似度检索。' +
          '提供 Collection/add_texts/query 等接口,纯 Python 轻量无需外部服务,适合本地 RAG 场景。' +
          '比 FAISS 更易用(带元数据存储),比专业向量库(如 Pinecone)更轻量。',
        apiPoints:
          'import chromadb\n' +
          '\n' +
          '# 创建客户端(内存/持久化)\n' +
          'client = chromadb.Client()\n' +
          '# client = chromadb.PersistentClient(path="./db")\n' +
          '\n' +
          '# 建集合, 加文档\n' +
          'col = client.create_collection("kb")\n' +
          'col.add_texts(\n' +
          '    texts=["苹果是水果", "汽车是交通工具"],\n' +
          '    ids=["1", "2"],\n' +
          ')\n' +
          '\n' +
          '# 相似度查询\n' +
          'results = col.query(\n' +
          '    query_texts=["水果"],\n' +
          '    n_results=2,\n' +
          ')',
        installHint: 'pip install chromadb',
        officialUrl: 'https://docs.trychroma.com/',
      },
    ],
  },
  {
    title: 'Agent 与多 Agent 编排',
    icon: '🤖',
    techs: [
      {
        name: 'CrewAI',
        matchKeys: ['crewai'],
        category: '多Agent框架',
        description:
          'CrewAI 是多 Agent 协作框架,定义 Agent(角色)/Task(任务)/Crew(团队)让多个 Agent 分工协作完成复杂任务。' +
          '比手写多 Agent 逻辑更简洁,内置任务分配、结果传递、工具共享机制。适合自动化工作流(如研究→写作→审校)。',
        apiPoints:
          'from crewai import Agent, Task, Crew\n' +
          '\n' +
          '# 定义 Agent(角色)\n' +
          'researcher = Agent(\n' +
          '    role="研究员",\n' +
          '    goal="收集资料",\n' +
          '    backstory="擅长调研",\n' +
          ')\n' +
          'writer = Agent(role="作家", goal="写文章", ...)\n' +
          '\n' +
          '# 定义任务\n' +
          'task = Task(description="写一篇AI报告", agent=writer)\n' +
          '\n' +
          '# 组队执行\n' +
          'crew = Crew(agents=[researcher, writer], tasks=[task])\n' +
          'result = crew.kickoff()',
        installHint: 'pip install crewai',
        officialUrl: 'https://docs.crewai.com/',
      },
    ],
  },
  {
    title: '工程化与可观测',
    icon: '⚙️',
    techs: [
      {
        name: 'Pydantic',
        matchKeys: ['pydantic'],
        category: '数据校验',
        description:
          'Python 数据校验与序列化库,用类型注解定义数据模型(BaseModel)并自动校验。' +
          'LLM 应用中常用于定义结构化输出 schema、工具参数、API 配置——让 LLM 输出符合预期格式。' +
          'FastAPI 也基于它做请求校验。',
        apiPoints:
          'from pydantic import BaseModel\n' +
          '\n' +
          '# 定义模型\n' +
          'class Person(BaseModel):\n' +
          '    name: str\n' +
          '    age: int\n' +
          '\n' +
          '# 校验+解析\n' +
          'p = Person(**{"name": "张三", "age": 30})\n' +
          'print(p.name, p.age)\n' +
          '\n' +
          '# 序列化\n' +
          'p.model_dump()       # dict\n' +
          'p.model_dump_json()  # JSON 字符串\n' +
          '\n' +
          '# LLM 结构化输出\n' +
          'response_format={"type": "json_object"}',
        installHint: 'pip install pydantic',
        officialUrl: 'https://docs.pydantic.dev/',
      },
      {
        name: 'tiktoken',
        matchKeys: ['tiktoken'],
        category: '工具库',
        description:
          'OpenAI 开源的快速 BPE 分词器,能把文本切成模型识别的 token 并计数。' +
          '用于估算 API 调用成本、控制上下文长度、管理对话历史窗口(超长时截断旧消息)。',
        apiPoints:
          'import tiktoken\n' +
          '\n' +
          '# 获取编码器(按模型)\n' +
          'enc = tiktoken.encoding_for_model("deepseek-v4-pro")\n' +
          '\n' +
          '# 编码/计数\n' +
          'tokens = enc.encode("Hello, world!")\n' +
          'print(len(tokens))  # token 数\n' +
          '\n' +
          '# 解码\n' +
          'text = enc.decode(tokens)\n' +
          '\n' +
          '# 估算成本\n' +
          'cost = len(tokens) * 0.00003',
        installHint: 'pip install tiktoken',
        officialUrl: 'https://github.com/openai/tiktoken',
      },
      {
        name: 'FastAPI',
        matchKeys: ['fastapi'],
        category: 'Web 框架',
        description:
          '现代 Python Web 框架,基于类型注解自动生成 API 文档与请求校验(依赖 Pydantic)。' +
          '用于把 LLM 应用部署成 HTTP 服务,性能高、开发快。本项目后端即基于 FastAPI。',
        apiPoints:
          'from fastapi import FastAPI\n' +
          'from pydantic import BaseModel\n' +
          '\n' +
          'app = FastAPI()\n' +
          '\n' +
          'class ChatReq(BaseModel):\n' +
          '    message: str\n' +
          '\n' +
          '@app.post("/chat")\n' +
          'def chat(req: ChatReq):\n' +
          '    return {"reply": f"你说: {req.message}"}\n' +
          '\n' +
          '# 启动\n' +
          'uvicorn app:app --port 4200',
        installHint: 'pip install fastapi',
        officialUrl: 'https://fastapi.tiangolo.com/',
      },
      {
        name: 'Docker',
        matchKeys: ['docker'],
        category: '容器化',
        description:
          '容器化平台,把应用与依赖打包成隔离环境运行。' +
          '本项目用 Docker 沙箱隔离执行学习者代码(网络隔离/只读文件系统/资源限制/超时),保证安全。也用于部署。',
        apiPoints:
          '# 构建镜像\n' +
          'docker build -t myapp .\n' +
          '\n' +
          '# 运行容器\n' +
          'docker run --rm -i myapp\n' +
          '\n' +
          '# 安全沙箱参数(本项目用)\n' +
          '--network=none      # 网络隔离\n' +
          '--read-only         # 只读文件系统\n' +
          '--memory=256m       # 内存限制\n' +
          '--cap-drop=ALL      # 去掉所有权限',
        installHint: '安装 Docker Desktop',
        officialUrl: 'https://www.docker.com/',
      },
      {
        name: 'pytest',
        matchKeys: ['pytest'],
        category: '测试框架',
        description:
          'Python 最主流的测试框架,用 assert 断言 + 函数名 test_ 即可写测试,无需类。' +
          'LLM 应用中常用于验证工具函数、解析器、RAG 检索结果、Agent 行为——保证代码改动不破坏已有功能。' +
          '配合 pytest.mark.parametrize 可批量测多组输入。',
        apiPoints:
          '# 测试文件 test_tools.py\n' +
          'import pytest\n' +
          'from myapp import parse_tool_args\n' +
          '\n' +
          'def test_parse_valid():\n' +
          '    args = parse_tool_args(\'{"city": "北京"}\')\n' +
          '    assert args["city"] == "北京"\n' +
          '\n' +
          '@pytest.mark.parametrize("s,exp", [\n' +
          '    ("1+1=?", 2),\n' +
          '    ("2*3=?", 6),\n' +
          '])\n' +
          'def test_math(s, exp):\n' +
          '    assert compute(s) == exp\n' +
          '\n' +
          '# 运行: pytest -v',
        installHint: 'pip install pytest',
        officialUrl: 'https://docs.pytest.org/',
      },
      {
        name: 'OpenTelemetry',
        matchKeys: ['opentelemetry'],
        category: '可观测性',
        description:
          '开源可观测性标准框架,统一采集 Trace(链路追踪)/Metrics(指标)/Logs(日志)三类信号。' +
          '在 LLM 应用中给每次模型调用、工具调用打上 span,就能看清整个请求链路在哪一步慢、哪一步出错。' +
          '与 Prometheus/Grafana 配合构成完整的可观测栈。',
        apiPoints:
          'from opentelemetry import trace\n' +
          'from opentelemetry.sdk.trace import TracerProvider\n' +
          '\n' +
          '# 初始化 Tracer\n' +
          'trace.set_tracer_provider(TracerProvider())\n' +
          'tracer = trace.get_tracer("llm-app")\n' +
          '\n' +
          '# 给 LLM 调用加 span\n' +
          'with tracer.start_as_current_span("llm.chat"):\n' +
          '    response = client.chat.completions.create(...)\n' +
          '    span.set_attribute("tokens", response.usage.total_tokens)',
        installHint: 'pip install opentelemetry-api opentelemetry-sdk',
        officialUrl: 'https://opentelemetry.io/',
      },
      {
        name: 'Tenacity',
        matchKeys: ['tenacity'],
        category: '重试库',
        description:
          'Python 通用重试库,用装饰器为任意函数加自动重试:指数退避、最大次数、捕获指定异常、超时等。' +
          'LLM API 调用常因网络抖动/限流失败,重试是提升系统鲁棒性(error resilience)的核心手段。' +
          '比手写 while+time.sleep 更简洁可靠。',
        apiPoints:
          'from tenacity import (\n' +
          '    retry, stop_after_attempt, wait_exponential\n' +
          ')\n' +
          '\n' +
          '# 最多重试 3 次, 指数退避 1s/2s/4s\n' +
          '@retry(\n' +
          '    stop=stop_after_attempt(3),\n' +
          '    wait=wait_exponential(multiplier=1, max=8),\n' +
          '    retry_on_exception=lambda e: isinstance(e, TimeoutError),\n' +
          ')\n' +
          'def call_llm(prompt: str) -> str:\n' +
          '    return client.chat.completions.create(...)',
        installHint: 'pip install tenacity',
        officialUrl: 'https://tenacity.readthedocs.io/',
      },
      {
        name: 'structlog',
        matchKeys: ['structlog'],
        category: '日志库',
        description:
          '结构化日志库,把日志输出成 JSON 键值对(而非纯文本),方便机器解析与检索。' +
          'LLM 应用中用它记录每次调用的模型/耗时/token 数/错误码,可观测性与排查效率远高于 print。' +
          '可与标准 logging、OpenTelemetry 无缝集成。',
        apiPoints:
          'import structlog\n' +
          '\n' +
          'log = structlog.get_logger()\n' +
          '\n' +
          '# 结构化字段\n' +
          'log.info(\n' +
          '    "llm_call",\n' +
          '    model="deepseek-v4-pro",\n' +
          '    latency_ms=320,\n' +
          '    tokens=512,\n' +
          ')\n' +
          '# 输出: {"event": "llm_call", "model": ..., "latency_ms": ...}',
        installHint: 'pip install structlog',
        officialUrl: 'https://www.structlog.org/',
      },
      {
        name: 'Prometheus',
        matchKeys: ['prometheus'],
        category: '监控系统',
        description:
          '开源监控与指标采集系统,按固定时间间隔拉取指标(如请求数/延迟/错误率),存时序数据库并支持查询。' +
          'LLM 服务用它监控调用量、token 消耗、P99 延迟等关键指标,是生产级可观测性的标准组件。',
        apiPoints:
          '# 指标定义与暴露(prometheus_client)\n' +
          'from prometheus_client import (\n' +
          '    Counter, Histogram, start_http_server\n' +
          ')\n' +
          '\n' +
          'calls = Counter("llm_calls_total", "LLM 调用次数")\n' +
          'latency = Histogram("llm_latency_seconds", "调用延迟")\n' +
          '\n' +
          'def call_model():\n' +
          '    with latency.time():\n' +
          '        resp = client.chat.completions.create(...)\n' +
          '    calls.inc()\n' +
          '\n' +
          '# 暴露指标: http://localhost:8000/metrics\n' +
          'start_http_server(8000)',
        installHint: 'pip install prometheus-client',
        officialUrl: 'https://prometheus.io/',
      },
      {
        name: 'Grafana',
        matchKeys: ['grafana'],
        category: '可视化面板',
        description:
          '开源数据可视化平台,把 Prometheus 等数据源画成实时监控面板/告警规则。' +
          'LLM 服务用它展示调用量趋势、token 消耗、延迟分布,让系统状态一目了然。' +
          '与 Prometheus 是监控黄金搭档。',
        apiPoints:
          '# 配置(provisioning/datasource.yml)\n' +
          'apiVersion: 1\n' +
          'datasources:\n' +
          '  - name: Prometheus\n' +
          '    type: prometheus\n' +
          '    url: http://prometheus:9090\n' +
          '\n' +
          '# 运行\n' +
          'docker run -p 3000:3000 grafana/grafana\n' +
          '# 浏览器打开 http://localhost:3000 配置面板',
        installHint: 'docker run -p 3000:3000 grafana/grafana',
        officialUrl: 'https://grafana.com/',
      },
      {
        name: 'Redis',
        matchKeys: ['redis'],
        category: '缓存/存储',
        description:
          '内存键值数据库,读写纳秒级,支持字符串/列表/哈希/过期时间等数据结构。' +
          'LLM 应用常用于缓存对话历史、限流计数、消息队列(多 Agent 通信),是提升吞吐与状态的标配。',
        apiPoints:
          'import redis\n' +
          '\n' +
          'r = redis.Redis(host="localhost", port=6379, decode_responses=True)\n' +
          '\n' +
          '# 缓存对话记录(带过期)\n' +
          'r.set("session:1", "你好", ex=3600)\n' +
          '\n' +
          '# 消息队列(多 Agent 通信)\n' +
          'r.lpush("agent:queue", "任务1")\n' +
          'msg = r.brpop("agent:queue", timeout=5)\n' +
          '\n' +
          '# 限流计数\n' +
          'r.incr("rate:key")',
        installHint: 'pip install redis && docker run -d -p 6379:6379 redis',
        officialUrl: 'https://redis.io/',
      },
      {
        name: 'JSON Lines',
        matchKeys: ['json lines', 'jsonl'],
        category: '数据格式',
        description:
          'JSON Lines(JSONL)格式:每行一个独立 JSON 对象,适合逐条追加/流式处理的日志与数据集。' +
          'LLM 场景常用于保存对话日志、训练样本集、任务输出——每行可独立解析,可增量写入,便于大文件处理。',
        apiPoints:
          '# 写入 JSONL(每行一个对象)\n' +
          'import json\n' +
          '\n' +
          'with open("logs.jsonl", "a", encoding="utf-8") as f:\n' +
          '    f.write(json.dumps({"role": "user", "content": "你好"}) + "\\n")\n' +
          '    f.write(json.dumps({"role": "assistant", "content": "你好!"}) + "\\n")\n' +
          '\n' +
          '# 逐行读取\n' +
          'with open("logs.jsonl", encoding="utf-8") as f:\n' +
          '    for line in f:\n' +
          '        record = json.loads(line)\n' +
          '        print(record["role"], record["content"])',
        installHint: 'Python 内置 json 即可',
        officialUrl: 'https://jsonlines.org/',
      },
    ],
  },
  {
    title: '部署与上线',
    icon: '🚀',
    techs: [
      {
        name: 'Docker Compose',
        matchKeys: ['docker compose', 'docker-compose'],
        category: '容器编排',
        description:
          'Docker 官方多容器编排工具,用一份 docker-compose.yml 定义并一键启动整个服务栈(后端/前端/数据库/缓存)。' +
          '是 LLM 应用交付的标准方式,本地开发与生产部署共用同一套配置。',
        apiPoints:
          '# docker-compose.yml\n' +
          'services:\n' +
          '  backend:\n' +
          '    build: ./backend\n' +
          '    ports: ["4200:4200"]\n' +
          '    depends_on:\n' +
          '      - redis\n' +
          '      - postgres\n' +
          '  redis:\n' +
          '    image: redis:7\n' +
          '\n' +
          '# 启动/停止整个服务栈\n' +
          'docker compose up -d\n' +
          'docker compose down',
        installHint: 'Docker Desktop 自带 / pip install docker-compose',
        officialUrl: 'https://docs.docker.com/compose/',
      },
      {
        name: 'PyYAML',
        matchKeys: ['pyyaml', 'yaml'],
        category: '配置解析',
        description:
          'Python 的 YAML 解析库,读写 yaml 配置文件(prompt 模板/模型参数/数据源配置)。' +
          '比 JSON 更易读(支持注释/锚点),是配置文件的常用格式。',
        apiPoints:
          'import yaml\n' +
          '\n' +
          '# 读配置\n' +
          'with open("config.yaml", encoding="utf-8") as f:\n' +
          '    cfg = yaml.safe_load(f)\n' +
          '    model_name = cfg["model"]["name"]\n' +
          '\n' +
          '# 写配置\n' +
          'with open("out.yaml", "w", encoding="utf-8") as f:\n' +
          '    yaml.safe_dump(cfg, f, allow_unicode=True)',
        installHint: 'pip install pyyaml',
        officialUrl: 'https://pyyaml.org/',
      },
      {
        name: 'Git',
        matchKeys: ['git'],
        category: '版本控制',
        description:
          '分布式版本控制系统,跟踪代码变更、支持多人协作与分支管理。' +
          '所有技术项目的基础设施,配合 GitHub/Gitee 实现托管与协作。',
        apiPoints:
          'git init              # 初始化仓库\n' +
          'git add .             # 暂存改动\n' +
          'git commit -m "feat: 新增检索功能"\n' +
          'git branch feature/rag  # 新建分支\n' +
          'git push origin main   # 推送到远程',
        installHint: '官网安装 Git',
        officialUrl: 'https://git-scm.com/',
      },
      {
        name: 'OpenAPI',
        matchKeys: ['openapi'],
        category: 'API 规范',
        description:
          '描述 REST API 的开放规范(Swagger 的继承者)。' +
          'FastAPI 基于类型注解自动生成 OpenAPI schema,并提供 /docs(Swagger UI)交互式调试页面。',
        apiPoints:
          '# FastAPI 自动生成 OpenAPI\n' +
          '@app.get("/api/course")\n' +
          'def get_course():\n' +
          '    return {...}\n' +
          '\n' +
          '# 自动提供:\n' +
          '#   /openapi.json - 机器可读规范\n' +
          '#   /docs        - Swagger UI 交互文档',
        installHint: 'pip install fastapi',
        officialUrl: 'https://www.openapis.org/',
      },
    ],
  },
  {
    title: '数据计算与可视化',
    icon: '📊',
    techs: [
      {
        name: 'NumPy',
        matchKeys: ['numpy'],
        category: '数值计算',
        description:
          'Python 科学计算基础库,提供高效的多维数组(ndarray)与矩阵运算。' +
          '几乎所有数据/AI 库的底层依赖,向量化运算比 Python 循环快百倍。',
        apiPoints:
          'import numpy as np\n' +
          '\n' +
          '# 数组\n' +
          'a = np.array([1, 2, 3])\n' +
          'b = np.zeros((3, 4))\n' +
          '\n' +
          '# 矩阵运算\n' +
          'np.dot(a, b)      # 矩阵乘\n' +
          'np.mean(a)        # 均值\n' +
          'a @ b             # 也是矩阵乘\n' +
          '\n' +
          '# 向量运算(嵌入场景)\n' +
          'cos_sim = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))',
        installHint: 'pip install numpy',
        officialUrl: 'https://numpy.org/',
      },
    ],
  },
  {
    title: 'Python 标准库',
    icon: '📦',
    techs: [
      {
        name: 'dataclasses',
        matchKeys: ['dataclasses'],
        category: '标准库',
        description:
          'Python 标准库的数据类,用 @dataclass 装饰器快速定义数据容器类,自动生成 __init__/__repr__ 等方法。' +
          '比手写类简洁,适合定义配置/状态/消息等结构化数据。',
        apiPoints:
          'from dataclasses import dataclass\n' +
          '\n' +
          '@dataclass\n' +
          'class Message:\n' +
          '    role: str\n' +
          '    content: str\n' +
          '    timestamp: float = 0.0\n' +
          '\n' +
          '# 自动生成 __init__\n' +
          'msg = Message(role="user", content="你好")\n' +
          'print(msg.role, msg.content)',
        installHint: 'Python 内置',
        officialUrl: 'https://docs.python.org/3/library/dataclasses.html',
      },
      {
        name: 'abc',
        matchKeys: ['abc'],
        category: '标准库',
        description:
          'Python 标准库的抽象基类(ABC)模块,用 ABCMeta 定义接口契约,强制子类实现指定方法(@abstractmethod)。' +
          '多 Agent 框架常用来定义 Agent 接口,保证所有 Agent 都有统一的方法签名。',
        apiPoints:
          'from abc import ABC, abstractmethod\n' +
          '\n' +
          'class Agent(ABC):\n' +
          '    @abstractmethod\n' +
          '    def run(self, task: str) -> str:\n' +
          '        """所有 Agent 必须实现 run 方法"""\n' +
          '        pass\n' +
          '\n' +
          'class MyAgent(Agent):\n' +
          '    def run(self, task):\n' +
          '        return f"处理: {task}"',
        installHint: 'Python 内置',
        officialUrl: 'https://docs.python.org/3/library/abc.html',
      },
    ],
  },
  {
    title: '其他工具',
    icon: '🛠️',
    techs: [
      {
        name: 'Mermaid',
        matchKeys: ['mermaid'],
        category: '图表工具',
        description:
          '用文本语法绘制流程图/时序图/架构图的工具,广泛用于文档与 Markdown。' +
          'LLM 项目中常用它画数据流图、Agent 协作流程、架构图,比手画图更易版本管理。',
        apiPoints:
          '```mermaid\n' +
          'graph LR\n' +
          '    A[用户提问] --> B[检索]\n' +
          '    B --> C[LLM生成]\n' +
          '    C --> D[返回答案]\n' +
          '```\n' +
          '\n' +
          '# 时序图\n' +
          'sequenceDiagram\n' +
          '    User->>Agent: 提问\n' +
          '    Agent->>Tool: 调用\n' +
          '    Tool-->>Agent: 结果\n' +
          '    Agent-->>User: 回答',
        installHint: 'Markdown 编辑器内置 / npm i mermaid',
        officialUrl: 'https://mermaid.js.org/',
      },
      {
        name: 'Markdown',
        matchKeys: ['markdown'],
        category: '文档格式',
        description:
          '轻量级标记语言,用简单符号写出结构化文档(标题/列表/代码块/表格/链接)。' +
          '是技术文档、README、笔记的事实标准。LLM 项目中用于写需求文档、API 文档、复盘记录。',
        apiPoints:
          '# 一级标题\n' +
          '## 二级标题\n' +
          '\n' +
          '- 列表项\n' +
          '- 列表项\n' +
          '\n' +
          '`行内代码` 和:\n' +
          '```\n' +
          '代码块\n' +
          '```\n' +
          '\n' +
          '[链接](url) | **加粗** | *斜体*',
        installHint: '',
        officialUrl: 'https://www.markdownguide.org/',
      },
    ],
  },
  {
    title: '额外知识点',
    icon: '📚',
    techs: [
      {
        name: 'langchain-community',
        matchKeys: ['langchain-community', 'langchain_community'],
        category: '社区集成',
        description:
          'LangChain 社区集成包,提供第三方向量库/文档加载器/嵌入模型等集成。' +
          '官方包未内置的组件(如 FAISS、PyPDFLoader)都从这里导入。',
        apiPoints:
          'from langchain_community.vectorstores import FAISS\n' +
          'from langchain_community.document_loaders import PyPDFLoader\n' +
          '\n' +
          '# 加载 PDF 文档\n' +
          'loader = PyPDFLoader("doc.pdf")\n' +
          'docs = loader.load()\n' +
          '\n' +
          '# 构建向量库\n' +
          'db = FAISS.from_documents(docs, embeddings)',
        installHint: 'pip install langchain-community',
        officialUrl: 'https://python.langchain.com/docs/integrations/',
      },
      {
        name: 'FAISS',
        matchKeys: ['faiss'],
        category: '向量检索',
        description:
          'Facebook AI 开源的向量相似度检索库,在内存中构建索引实现高效最近邻搜索。' +
          'RAG 场景的标配向量库,支持 L2/内积等距离度量与 GPU 加速。',
        apiPoints:
          'import faiss\n' +
          '\n' +
          'dim = 768\n' +
          'index = faiss.IndexFlatL2(dim)\n' +
          'index.add(vectors)          # 加入向量\n' +
          '\n' +
          'D, I = index.search(query, k)  # 返回距离与索引',
        installHint: 'pip install faiss-cpu',
        officialUrl: 'https://faiss.ai/',
      },
      {
        name: 'pypdf',
        matchKeys: ['pypdf'],
        category: '文档处理',
        description:
          '纯 Python 的 PDF 解析库,提取文本/元数据/页面信息。' +
          'RAG 知识库构建时常用的 PDF 文档加载底层库。',
        apiPoints:
          'from pypdf import PdfReader\n' +
          '\n' +
          'reader = PdfReader("report.pdf")\n' +
          'for page in reader.pages:\n' +
          '    text = page.extract_text()\n' +
          '    print(text)',
        installHint: 'pip install pypdf',
        officialUrl: 'https://pypdf.readthedocs.io/',
      },
      {
        name: 'logging',
        matchKeys: ['logging'],
        category: '标准库',
        description:
          'Python 标准库日志模块,用于记录 LLM 应用的调用链/错误/性能,是可观测性(Observability)的基础。' +
          '比 print 更规范可控(可配级别/格式/文件/时间),生产环境排查问题必备。',
        apiPoints:
          'import logging\n' +
          '\n' +
          '# 基础配置\n' +
          'logging.basicConfig(\n' +
          '    level=logging.INFO,\n' +
          '    format="%(asctime)s [%(levelname)s] %(message)s",\n' +
          ')\n' +
          '\n' +
          'logger = logging.getLogger(__name__)\n' +
          'logger.info("调用模型")\n' +
          'logger.error("调用失败: %s", err)',
        installHint: 'Python 内置',
        officialUrl: 'https://docs.python.org/3/library/logging.html',
      },
      {
        name: 'requests',
        matchKeys: ['requests'],
        category: 'HTTP库',
        description:
          'Python 最常用的 HTTP 客户端库,用于调用 REST API。' +
          'LLM 场景常用于直接调模型接口(不用 SDK)或抓取网页数据做知识库。',
        apiPoints:
          'import requests\n' +
          '\n' +
          '# GET 请求\n' +
          'resp = requests.get("https://api.example.com/data")\n' +
          'data = resp.json()\n' +
          '\n' +
          '# POST 请求(调模型接口)\n' +
          'resp = requests.post(\n' +
          '    "https://api.deepseek.com/chat/completions",\n' +
          '    headers={"Authorization": f"Bearer {key}"},\n' +
          '    json={"model": "deepseek-v4-pro", "messages": [...]},\n' +
          ')',
        installHint: 'pip install requests',
        officialUrl: 'https://docs.python-requests.org/',
      },
      {
        name: 'PyTorch',
        matchKeys: ['torch'],
        category: '深度学习框架',
        description:
          'PyTorch 是主流深度学习框架,提供张量(Tensor)计算与自动求导(autograd)。' +
          '用于训练/微调神经网络,定义层与前向传播。是 transformers/peft 等库的底层,自建小模型的基础。',
        apiPoints:
          'import torch\n' +
          'import torch.nn as nn\n' +
          '\n' +
          '# 张量\n' +
          'x = torch.tensor([1.0, 2.0, 3.0])\n' +
          '\n' +
          '# 定义网络\n' +
          'class Net(nn.Module):\n' +
          '    def __init__(self):\n' +
          '        super().__init__()\n' +
          '        self.fc = nn.Linear(10, 1)\n' +
          '    def forward(self, x):\n' +
          '        return self.fc(x)\n' +
          '\n' +
          '# 训练\n' +
          'loss.backward()\n' +
          'optimizer.step()',
        installHint: 'pip install torch',
        officialUrl: 'https://pytorch.org/',
      },
      {
        name: 'transformers',
        matchKeys: ['transformers'],
        category: '模型库',
        description:
          'Hugging Face 出品的预训练模型库,提供海量模型(GPT/BERT/Llama 等)的加载/微调/推理接口。' +
          '是自建/微调小模型的核心工具,一行代码加载世界级预训练模型。',
        apiPoints:
          'from transformers import (\n' +
          '    AutoModel, AutoTokenizer, pipeline\n' +
          ')\n' +
          '\n' +
          '# 加载模型+分词器\n' +
          'model = AutoModel.from_pretrained("bert-base")\n' +
          'tokenizer = AutoTokenizer.from_pretrained("bert-base")\n' +
          '\n' +
          '# 快速推理(pipeline)\n' +
          'pipe = pipeline("text-classification")\n' +
          'result = pipe("这个电影很好看")',
        installHint: 'pip install transformers',
        officialUrl: 'https://huggingface.co/docs/transformers',
      },
      {
        name: 'PEFT',
        matchKeys: ['peft'],
        category: '微调库',
        description:
          'Parameter-Efficient Fine-Tuning 库,用 LoRA/Prefix-Tuning 等方法只训练极少参数(通常<1%)即可微调大模型。' +
          '大幅降低显存与算力需求,让个人电脑也能微调 7B 模型。',
        apiPoints:
          'from peft import LoraConfig, get_peft_model\n' +
          '\n' +
          '# 配置 LoRA\n' +
          'config = LoraConfig(\n' +
          '    r=8,\n' +
          '    lora_alpha=16,\n' +
          '    target_modules=["q_proj", "v_proj"],\n' +
          ')\n' +
          '\n' +
          '# 包装模型(只训练 LoRA 参数)\n' +
          'model = get_peft_model(base_model, config)\n' +
          '\n' +
          '# 正常训练即可, 只更新少量参数',
        installHint: 'pip install peft',
        officialUrl: 'https://huggingface.co/docs/peft',
      },
      {
        name: 'scikit-learn',
        matchKeys: ['scikit-learn'],
        category: '机器学习库',
        description:
          '经典机器学习库,提供分类/回归/聚类/降维(PCA)等算法。' +
          'LLM 场景常用于嵌入可视化(PCA 降维到 2D)、相似度计算、评估指标。',
        apiPoints:
          'from sklearn.decomposition import PCA\n' +
          'from sklearn.metrics.pairwise import cosine_similarity\n' +
          '\n' +
          '# PCA 降维(嵌入可视化)\n' +
          'pca = PCA(n_components=2)\n' +
          'coords = pca.fit_transform(embeddings)\n' +
          '\n' +
          '# 余弦相似度\n' +
          'sim = cosine_similarity([v1], [v2])[0][0]',
        installHint: 'pip install scikit-learn',
        officialUrl: 'https://scikit-learn.org/',
      },
      {
        name: 'matplotlib',
        matchKeys: ['matplotlib'],
        category: '可视化',
        description:
          'Python 绑图库,用于绘制散点图/曲线图/柱状图等。' +
          'LLM 场景常用于嵌入空间可视化、训练曲线展示。',
        apiPoints:
          'import matplotlib.pyplot as plt\n' +
          '\n' +
          '# 散点图(嵌入可视化)\n' +
          'plt.figure(figsize=(8, 6))\n' +
          'plt.scatter(x, y)\n' +
          'plt.title("嵌入空间")\n' +
          'plt.xlabel("PC1")\n' +
          'plt.ylabel("PC2")\n' +
          'plt.show()\n' +
          '\n' +
          '# 曲线图(训练损失)\n' +
          'plt.plot(losses)\n' +
          'plt.title("训练损失")',
        installHint: 'pip install matplotlib',
        officialUrl: 'https://matplotlib.org/',
      },
      {
        name: 'concurrent.futures',
        matchKeys: ['concurrent.futures'],
        category: '标准库',
        description:
          'Python 标准库并发执行模块,提供 ThreadPoolExecutor(线程池)/ProcessPoolExecutor(进程池)实现并行调用。' +
          '用于多 Agent 并发执行提升效率,或批量 LLM 调用提速。',
        apiPoints:
          'from concurrent.futures import (\n' +
          '    ThreadPoolExecutor, as_completed\n' +
          ')\n' +
          '\n' +
          '# 线程池并发(适合 IO 密集, 如 API 调用)\n' +
          'with ThreadPoolExecutor(max_workers=4) as ex:\n' +
          '    futures = [ex.submit(call_llm, q) for q in questions]\n' +
          '    for f in as_completed(futures):\n' +
          '        print(f.result())',
        installHint: 'Python 内置',
        officialUrl: 'https://docs.python.org/3/library/concurrent.futures.html',
      },
      {
        name: 'pytz',
        matchKeys: ['pytz'],
        category: '时区库',
        description:
          '时区处理库,提供全球时区数据库与转换。' +
          '用于工具函数获取指定时区时间,或处理跨时区的时间数据。',
        apiPoints:
          'import pytz\n' +
          'from datetime import datetime\n' +
          '\n' +
          '# 获取指定时区时间\n' +
          'tz = pytz.timezone("Asia/Shanghai")\n' +
          'now = datetime.now(tz)\n' +
          'print(now.strftime("%Y-%m-%d %H:%M:%S"))\n' +
          '\n' +
          '# 时区转换\n' +
          'utc_now = datetime.now(pytz.UTC)\n' +
          'beijing_time = utc_now.astimezone(tz)',
        installHint: 'pip install pytz',
        officialUrl: 'https://pythonhosted.org/pytz/',
      },
    ],
  },
]

/** 归一化技术名(用于匹配课程 techStack.name) */
export function normalizeTechName(name: string): string {
  return name.trim().toLowerCase().replace(/[-_]/g, ' ')
}

/** 全部技术扁平列表(便于查找) */
export const ALL_TECHS: TechInfo[] = TECH_GROUPS.flatMap((g) => g.techs)

/** 按归一化名查技术信息 */
export function findTech(name: string): TechInfo | undefined {
  const key = normalizeTechName(name)
  return ALL_TECHS.find((t) => t.matchKeys.some((k) => normalizeTechName(k) === key))
}
