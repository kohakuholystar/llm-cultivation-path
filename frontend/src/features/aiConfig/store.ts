import { create } from 'zustand'
import { persist } from 'zustand/middleware'

/**
 * 全局 AI 配置(本地 localStorage 优先)。
 *
 * 学习者在前端填一次 API key / base_url / model,
 * 后续所有任务跑沙箱时由前端注入到容器 env, 全局复用。
 * 不填则 fallback 到后端 .env 的配置。
 */

// DeepSeek 为默认(便宜 + OpenAI 兼容接口)
const DEFAULT_BASE_URL = 'https://api.deepseek.com'
const DEFAULT_MODEL = 'deepseek-v4-pro'

interface AiConfigState {
  /** API key(明文存 localStorage, 本地优先, 不上传) */
  apiKey: string
  /** API 接口地址(OpenAI 兼容) */
  baseUrl: string
  /** 模型名 */
  model: string
  /** 是否已完成首次配置(用于引导弹窗) */
  configured: boolean
  /** 配置弹窗是否打开(全局可控, 任何组件能触发) */
  modalOpen: boolean
}

interface AiConfigActions {
  setConfig: (cfg: Partial<Pick<AiConfigState, 'apiKey' | 'baseUrl' | 'model'>>) => void
  /** 标记为已配置(用户点过保存即算) */
  markConfigured: () => void
  /** 重置为默认值(清空 key) */
  reset: () => void
  /** 打开/关闭配置弹窗 */
  setModalOpen: (open: boolean) => void
}

type AiConfigStore = AiConfigState & AiConfigActions

const defaultState: AiConfigState = {
  apiKey: '',
  baseUrl: DEFAULT_BASE_URL,
  model: DEFAULT_MODEL,
  configured: false,
  modalOpen: false,
}

export const useAiConfig = create<AiConfigStore>()(
  persist(
    (set) => ({
      ...defaultState,

      setConfig: (cfg) =>
        set((s) => ({
          ...s,
          ...cfg,
          // 改了配置视为已配置
          configured: true,
        })),

      markConfigured: () => set({ configured: true }),

      reset: () => set({ ...defaultState }),

      setModalOpen: (open) => set({ modalOpen: open }),
    }),
    {
      name: 'llmquest-ai-config',
      version: 1,
      // modalOpen 不持久化(每次刷新默认关闭)
      partialize: (s) => ({
        apiKey: s.apiKey,
        baseUrl: s.baseUrl,
        model: s.model,
        configured: s.configured,
      }),
    },
  ),
)

/** 便捷选择器: 当前是否已填 key(决定是否 fallback 后端 .env) */
export const useHasApiKey = () => useAiConfig((s) => s.apiKey.trim().length > 0)

export { DEFAULT_BASE_URL, DEFAULT_MODEL }
