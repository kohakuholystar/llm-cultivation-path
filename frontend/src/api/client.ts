import type { Course, Chapter, Task, SandboxRunRequest, SandboxRunResponse, StepValidationResponse } from '@shared/types'

// 开发环境走 vite proxy(/api → 后端4200, 见 vite.config.ts), 用相对路径即可。
// 仅当显式设置了 VITE_API_BASE_URL(如部署到不同域名)时才用绝对 URL。
// 子路径部署时(云端 /llm-cultivation-path/)API 走同级子路径, 由 Caddy strip 前缀反代到后端。
const BASE = import.meta.env.VITE_API_BASE_URL || import.meta.env.BASE_URL.replace(/\/$/, '')

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${url}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  })
  if (!resp.ok) {
    const text = await resp.text()
    // FastAPI HTTPException 的可读 detail 直接抛给界面展示(如口令错误/限流提示)
    try {
      const detail = JSON.parse(text)?.detail
      if (detail) throw new Error(`${resp.status}: ${detail}`)
    } catch (e) {
      if (e instanceof SyntaxError) throw new Error(`${resp.status}: ${text}`)
      throw e
    }
    throw new Error(`${resp.status}: ${text}`)
  }
  return resp.json()
}

export const api = {
  health: () =>
    fetchJson<{ status: string; version: string; sandboxReady: boolean }>('/api/health'),

  getCourse: () => fetchJson<Course>('/api/course'),
  getChapter: (id: string) => fetchJson<Chapter>(`/api/course/${id}`),
  getTask: (id: string) => fetchJson<Task>(`/api/task/${id}`),

  runSandbox: (req: SandboxRunRequest) =>
    fetchJson<SandboxRunResponse>('/api/sandbox/run', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  validateStep: (taskId: string, stepId: string, code: string, env?: Record<string, string>) =>
    fetchJson<StepValidationResponse>(`/api/task/${taskId}/step/${stepId}/validate`, {
      method: 'POST',
      body: JSON.stringify({ code, env }),
    }),
}
