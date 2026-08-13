# LLM Cultivation Path · LLM Agent 工程师学习之路

**A gamified, task-driven learning platform for the LLM stack — from your first API call to building a tiny model.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](backend/pyproject.toml)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](frontend/package.json)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](backend/pyproject.toml)
[![pnpm](https://img.shields.io/badge/pnpm-9+-F69220?logo=pnpm&logoColor=white)](package.json)

**English** | [简体中文](README.md)

Learn LLM engineering like leveling up in a game: 8 chapters, 39 hands-on tasks, real code running in a real sandbox. Write Python in the built-in IDE, call actual LLM APIs, pass validation rules, earn EXP, and unlock the next stage — no login, no server-side account, your progress stays in your browser.

![Hero](docs/screenshots/hero.png)

## ✨ Features

- ⚔️ **Gamified curriculum** — 8 chapters / 39 tasks / **212 steps** covering the full LLM stack, from API basics to a self-built tiny model
- 💻 **Built-in IDE** — Monaco Editor; every task ships with instructions, a checklist, hints, samples, and a reference solution
- 📜 **Learning-contract starters** — every starter file opens with the step's goal, what to fill in, key function signatures, the tech stack, and the expected observable result
- 🐳 **Real code execution** — your Python runs in a Docker sandbox (core / ml images) against the live DeepSeek API, with real stdout back
- ✅ **Smart validation** — static rules (AST / API-call / output matching) plus behavioral checks (sandbox runs + pytest) decide pass/fail precisely
- 🔑 **Bring your own key** — network tasks require your own DeepSeek key (kept in your browser, never stored server-side); there is no shared key to leech
- 🤖 **LLM-generated courseware** — the curriculum itself is produced by an LLM pipeline (`scripts/generate_curriculum.py`) with Pydantic validation
- 📦 **Local-first** — no sign-up; progress lives in `localStorage`
- 📖 **Full docs site** — installation guide, learning path, and a searchable tech reference for every library used

## 📸 Screenshots

| Task Workspace (IDE + instructions) | Course Map |
| :---: | :---: |
| ![Workspace](docs/screenshots/workspace.png) | ![Course map](docs/screenshots/course-map.png) |

| Tech Reference Docs |
| :---: |
| ![Docs](docs/screenshots/docs.png) |

## 🚀 Quick Start

**Prerequisites:** Node.js ≥ 20, pnpm ≥ 9, Python ≥ 3.12, Docker (optional, for the code sandbox)

```bash
# 1. Clone
git clone https://github.com/kohakushigure/llm-cultivation-path.git
cd llm-cultivation-path

# 2. Frontend deps
pnpm install

# 3. Backend (venv recommended)
cd backend
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
# source .venv/bin/activate                             # macOS / Linux
pip install -e ".[dev]"
cd ..

# 4. Run (two terminals)
pnpm dev:backend   # FastAPI on :4200
pnpm dev           # Vite on :3200
```

Open http://localhost:3200, click **开始学习**, and clear your first task.

**Optional — enable the code sandbox** (without it, tasks fall back to frontend validation):

```bash
pnpm build:sandbox   # builds the llmquest-sandbox Docker image
```

## 📦 Deployment

The section above is dev mode; for a **production-ish local/LAN deployment** (assumes Node ≥ 20, pnpm ≥ 9, Python ≥ 3.12):

```bash
# 1. Install deps and build the frontend (bakes the backend URL into the bundle)
pnpm install
VITE_API_BASE_URL=http://localhost:4200 pnpm build                  # Git Bash / macOS / Linux
# $env:VITE_API_BASE_URL="http://localhost:4200"; pnpm build        # Windows PowerShell

# 2. Start the backend (port 4200)
cd backend
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
# source .venv/bin/activate                             # macOS / Linux
pip install -e .
uvicorn app.main:app --host 0.0.0.0 --port 4200

# 3. Serve the frontend statically (second terminal; -s handles SPA route fallback)
npx serve -s frontend/dist -l 3200
```

Open http://localhost:3200.

- **Different port?** If the frontend isn't served on 3200, set the backend env var `CORS_ORIGINS` accordingly (default allows only `http://localhost:3200`).
- **Docker?** Docker is only used for the code-execution sandbox: `pnpm build:sandbox` (requires Docker Desktop). The app itself ships no image — the three steps above are all you need; without the sandbox image, execution tasks fall back to frontend validation.

## 🔑 API Key

Any OpenAI-compatible provider works (DeepSeek, Tongyi, Moonshot/Kimi, …). Either:

- click the **AI 配置** gear in the top-right corner of the site and paste your key, or
- copy `.env.example` to `.env` in the repo root:

```bash
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.deepseek.com
GENERATOR_MODEL=deepseek-v4-pro
```

## 🗺️ Curriculum

| Chapter | Theme |
| :--- | :--- |
| 1 · 项目起步 | LLM basics — DeepSeek setup, chat, streaming, structured output, token economics |
| 2 · 进入项目组 | LangChain — LCEL pipes, prompt templates, output parsers, memory, routing |
| 3 · 资料检索 | RAG — embeddings, vector stores, retrieval pipelines |
| 4 · 工具开发进阶 | Agent control — tools, structured calling, memory, human-in-the-loop |
| 5 · 运行时工程 | Harness engineering — context windows, error resilience, observability, plugins |
| 6 · 多 Agent 协作 | Multi-Agent — message bus, supervisor, debate patterns |
| 7 · 微型模型实验 | Build a tiny model — tokenizer, training loop, inference |
| 8 · 黑糖资料室 | Capstone — ship a complete LLM application |

## 🛠️ Tech Stack

| Layer | Tech |
| :--- | :--- |
| Frontend | React 18 · TypeScript · Vite · Tailwind CSS · Monaco Editor · Zustand |
| Backend | FastAPI · Pydantic v2 · OpenAI SDK · Uvicorn |
| Sandbox | Docker (isolated Python execution) |
| Tooling | pnpm workspace · pytest · Ruff |

## 📁 Project Structure

```
├── frontend/            # React SPA (Vite, port 3200)
│   └── src/pages|components|features|data
├── backend/             # FastAPI app (port 4200)
│   ├── app/routers|services|models
│   └── app/data/chapters/   # course content: 8 chapters, per-task starter/solution/tests
├── shared/              # Shared TypeScript types
├── scripts/             # LLM curriculum pipeline (generate / validate / verify)
├── docker/              # Code-execution sandbox image
└── docs/screenshots/
```

## 🧪 Tests & Quality

```bash
pnpm test        # backend pytest suite
pnpm typecheck   # TypeScript across workspaces
```

## 🤝 Contributing

Issues and PRs are welcome. If you add or rewrite course content, run the validators before submitting:

```bash
python scripts/validate_curriculum.py
python scripts/verify_solutions.py
```

## 📄 License

[MIT](LICENSE) © 2026 kohakushigure
