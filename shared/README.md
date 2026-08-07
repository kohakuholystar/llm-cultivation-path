# shared — 前后端共享层

本目录是类型的 **single source of truth**。

## 结构

```
shared/
├── types/
│   ├── course.ts     课程树(Course/Chapter/Task/Step/ValidationRule) — TS 权威
│   ├── sandbox.ts    沙箱请求/响应
│   ├── progress.ts   学习者进度 + 成就 + 等级公式
│   └── index.ts      汇总导出
└── schemas/          JSON Schema(M1 由后端 Pydantic 生成,用于 LLM 约束)
```

## 共享机制

| 方向 | 机制 |
|---|---|
| 前端 | 直接 `import { Course, Step } from '@shared/types'`(别名见 vite.config.ts) |
| 后端 | Pydantic 模型手工对齐 TS 定义(`backend/app/models/course.py`),`alias_generator=to_camel` 统一对外 camelCase |
| LLM 生成 | M1 用 `Course.model_json_schema()` 生成 JSON Schema,喂给 LLM 的 `response_format` |
| 运行时校验 | 后端用 Pydantic 校验课程 JSON;前端可选 ajv 校验 |

## 命名约定

- **TS**: camelCase
- **Python**: snake_case + `alias_generator=to_camel`,对外 API 一律 camelCase
- **JSON**: camelCase(前后端交换数据时)

## 修改类型时的检查清单

1. 改 `shared/types/*.ts`(TS 权威)
2. 同步改 `backend/app/models/course.py`(Pydantic 对齐)
3. 跑 `pnpm typecheck` + `cd backend && .venv/Scripts/python -m pytest`
4. 若结构 breaking,课程 JSON 的 `version` 要 +1,前端 progress 要写迁移
