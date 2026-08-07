import type { Course, Chapter, Task, SandboxRunRequest, SandboxRunResponse } from '@shared/types'

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
}
