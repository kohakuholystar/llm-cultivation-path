import type { Course, Chapter, Task, SandboxRunRequest, SandboxRunResponse } from '@shared/types'
import { useAiConfig } from '@/features/aiConfig/store'

// 开发环境走 vite proxy(/api → 后端4200, 见 vite.config.ts), 用相对路径即可。
// 仅当显式设置了 VITE_API_BASE_URL(如部署到不同域名)时才用绝对 URL。
const BASE = import.meta.env.VITE_API_BASE_URL || ''

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${url}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
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
      // 服务器版访问口令(后端未启用时为空串, 不产生影响)
      headers: { 'X-Access-Code': useAiConfig.getState().accessCode },
      body: JSON.stringify(req),
    }),
}
