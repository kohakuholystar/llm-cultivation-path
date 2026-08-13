# LLM Agent 工程师学习之路 · LLM Cultivation Path

**打怪升级式、任务驱动的 LLM 技术栈学习平台 —— 从第一次 API 调用,到自建一个小模型。**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](backend/pyproject.toml)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](frontend/package.json)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](backend/pyproject.toml)
[![pnpm](https://img.shields.io/badge/pnpm-9+-F69220?logo=pnpm&logoColor=white)](package.json)

[English](README.en.md) | **简体中文**

像打游戏一样闯关学 LLM 工程:8 章 39 个实战任务,真代码、真沙箱、真 API。在内置 IDE 里写 Python,调用真实的大模型接口,通过验证规则、赚取经验值、解锁下一关。无需注册登录,进度保存在你自己的浏览器里。

![首页](docs/screenshots/hero.png)

## ✨ 特色

- ⚔️ **游戏化课程** —— 8 章 39 任务 **212 步**,覆盖 LLM 全技术栈,从 API 基础一路打到自建小模型
- 💻 **内置 IDE** —— Monaco 编辑器;每个任务配说明、任务清单、提示、样例、术语和完整代码参考
- 📜 **学习契约模板** —— 每个 starter 顶部标明本步目标、补写内容、关键函数出入参、技术栈和可观察结果,动笔前就知道要做什么
- 🐳 **真实代码执行** —— Docker 沙箱(core / ml 双镜像)运行你的 Python,直连 DeepSeek 真实接口,看真实输出
- ✅ **智能通关验证** —— 静态规则(代码结构 / API 调用 / 输出匹配)+ 行为校验(沙箱实跑 + pytest),精准判定掌握度
- 🔑 **自己的 Key 自己的账** —— 联网课程必须填你自己的 DeepSeek Key(存浏览器,不过夜于服务器),没有公共 Key 可蹭
- 🤖 **LLM 生成课程** —— 课程内容本身由 LLM 管线生成(`scripts/generate_curriculum.py`),Pydantic 全程校验
- 📦 **本地优先** —— 无需登录,进度存浏览器 `localStorage`,数据在你手里
- 📖 **完整文档站** —— 安装指南、学习路径、以及每个用到的库的搜索式技术参考

## 📸 截图

| 学习工作区(IDE + 教学面板) | 课程地图 |
| :---: | :---: |
| ![工作区](docs/screenshots/workspace.png) | ![课程地图](docs/screenshots/course-map.png) |

| 技术参考文档 |
| :---: |
| ![文档](docs/screenshots/docs.png) |

## 🚀 快速开始

**环境要求:** Node.js ≥ 20、pnpm ≥ 9、Python ≥ 3.12、Docker(可选,用于代码沙箱)

```bash
# 1. 克隆
git clone https://github.com/kohakushigure/llm-cultivation-path.git
cd llm-cultivation-path

# 2. 前端依赖
pnpm install

# 3. 后端(建议 venv)
cd backend
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
# source .venv/bin/activate                             # macOS / Linux
pip install -e ".[dev]"
cd ..

# 4. 启动(两个终端)
pnpm dev:backend   # FastAPI,端口 4200
pnpm dev           # Vite,端口 3200
```

打开 http://localhost:3200   ,点 **开始学习**,通关你的第一个任务。

**可选 —— 启用代码沙箱**(不启用则部分任务降级为前端验证):

```bash
pnpm build:sandbox   # 构建 llmquest-sandbox Docker 镜像
```

## 📦 快速部署

上文「快速开始」是开发模式;下面是**生产部署**(本机/局域网,假设已有 Node ≥ 20、pnpm ≥ 9、Python ≥ 3.12):

```bash
# 1. 安装依赖并构建前端(把后端地址打进静态包)
pnpm install
VITE_API_BASE_URL=http://localhost:4200 pnpm build                  # Git Bash / macOS / Linux
# $env:VITE_API_BASE_URL="http://localhost:4200"; pnpm build        # Windows PowerShell

# 2. 启动后端(端口 4200)
cd backend
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
# source .venv/bin/activate                             # macOS / Linux
pip install -e .
uvicorn app.main:app --host 0.0.0.0 --port 4200

# 3. 静态托管前端(另开终端;-s 处理 SPA 路由回退)
npx serve -s frontend/dist -l 3200
```

访问 http://localhost:3200 即可。

- **换端口?** 前端若不用 3200,需同步设置后端环境变量 `CORS_ORIGINS`(默认只放行 `http://localhost:3200`)
- **Docker?** 本项目的 Docker 仅用于代码沙箱组件:`pnpm build:sandbox`(需 Docker Desktop)。应用本体不提供镜像,按上面三步部署即可;没有沙箱镜像也能正常运行,代码执行任务会降级为前端验证

## 🔑 API Key

支持任何 OpenAI 兼容厂商(DeepSeek、通义、Moonshot/Kimi……),二选一:

- 点网站右上角 **AI 配置** 直接填入,或
- 复制根目录 `.env.example` 为 `.env`:

```bash
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.deepseek.com
GENERATOR_MODEL=deepseek-v4-pro
```

## 🗺️ 学习路线

| 章节 | 内容 |
| :--- | :--- |
| 第一章 · 项目起步 | LLM 基础 —— DeepSeek 接入、多轮对话、流式输出、结构化输出、Token 经济学 |
| 第二章 · 进入项目组 | LangChain 架构 —— LCEL 管道、提示词模板、输出解析器、对话记忆、链路由 |
| 第三章 · 资料检索 | RAG 检索增强 —— 向量嵌入、向量库、检索管线 |
| 第四章 · 工具开发进阶 | Agent 智能体 —— 工具调用、结构化工具、记忆、人工介入 |
| 第五章 · 运行时工程 | Harness 工程 —— 上下文窗口、错误韧性、可观测性、插件架构 |
| 第六章 · 多 Agent 协作 | 消息总线、Supervisor、辩论模式 |
| 第七章 · 微型模型实验 | 自建小模型 —— 分词器、训练循环、推理 |
| 第八章 · 黑糖资料室 | 毕业设计 —— 完整交付一个 LLM 应用 |

## 🛠️ 技术栈

| 层 | 技术 |
| :--- | :--- |
| 前端 | React 18 · TypeScript · Vite · Tailwind CSS · Monaco Editor · Zustand |
| 后端 | FastAPI · Pydantic v2 · OpenAI SDK · Uvicorn |
| 沙箱 | Docker(隔离执行 Python) |
| 工程化 | pnpm workspace · pytest · Ruff |

## 📁 项目结构

```
├── frontend/            # React 单页应用(Vite,端口 3200)
│   └── src/pages|components|features|data
├── backend/             # FastAPI 应用(端口 4200)
│   ├── app/routers|services|models
│   └── app/data/chapters/   # 课程内容:8 章,每任务含 starter/solution/测试
├── shared/              # 前后端共享 TypeScript 类型
├── scripts/             # LLM 课程生成管线(生成 / 校验 / 答案验证)
├── docker/              # 代码执行沙箱镜像
└── docs/screenshots/
```

## 🧪 测试与质量

```bash
pnpm test        # 后端 pytest 测试套件
pnpm typecheck   # 全部 workspace 的 TypeScript 检查
```

## 🤝 参与贡献

欢迎 Issue 和 PR。如果新增或改写课程内容,提交前请先跑校验:

```bash
python scripts/validate_curriculum.py
python scripts/verify_solutions.py
```

## 📄 许可证

[MIT](LICENSE) © 2026 kohakushigure
