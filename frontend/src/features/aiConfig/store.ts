import { create } from 'zustand'
import { persist } from 'zustand/middleware'

/**
 * 全局 AI 配置(本地 localStorage 优先)。
 *
 * 学习者在前端填一次自己的 DeepSeek API key / model，
 * 后续联网任务跑沙箱时由前端注入到容器 env，全局复用。
 * 联网课程不使用后端 .env 兜底 Key。
 */

// DeepSeek 为默认(便宜 + OpenAI 兼容接口)
const DEFAULT_BASE_URL = 'https://api.deepseek.com'
const DEFAULT_MODEL = 'deepseek-v4-pro'

interface AiConfigState {
  /** API key(明文存 localStorage, 本地优先, 不上传) */
  apiKey: string
  /** API 接口地址（固定为 DeepSeek 官方端点） */
  baseUrl: string
  /** 模型名 */
  model: string
  /** 服务器版访问口令（邀请码）；服务器启用时必须填写。 */
  accessCode: string
  /** 是否由当前服务器启用邀请码门禁；启动时查询（404 即视为关闭），不持久化。 */
  inviteRequired: boolean
  /** 配置弹窗是否打开(全局可控, 任何组件能触发) */
  modalOpen: boolean
}

interface AiConfigActions {
  setConfig: (cfg: Partial<Pick<AiConfigState, 'apiKey' | 'baseUrl' | 'model' | 'accessCode'>>) => void
  setInviteRequired: (required: boolean) => void
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
  accessCode: '',
  inviteRequired: false,
  modalOpen: false,
}

export const useAiConfig = create<AiConfigStore>()(
  persist(
    (set) => ({
      ...defaultState,

      setConfig: (cfg) => set((s) => ({ ...s, ...cfg })),

      setInviteRequired: (inviteRequired) => set({ inviteRequired }),

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
        accessCode: s.accessCode,
      }),
    },
  ),
)

/** 便捷选择器: 当前配置是否可用于真实 DeepSeek 联网课程。 */
export const useHasDeepSeekConfig = () =>
  useAiConfig((s) => {
    const baseUrl = s.baseUrl.trim().replace(/\/+$/, '')
    return Boolean(s.apiKey.trim()) && baseUrl === DEFAULT_BASE_URL && s.model.trim().startsWith('deepseek-')
  })

/** 全站使用门禁：自己的 DeepSeek 配置与云端邀请码都必须满足。 */
export const useHasSystemConfig = () =>
  useAiConfig((s) => {
    const baseUrl = s.baseUrl.trim().replace(/\/+$/, '')
    const hasInvite = !s.inviteRequired || Boolean(s.accessCode.trim())
    return Boolean(s.apiKey.trim()) && hasInvite &&
      baseUrl === DEFAULT_BASE_URL && s.model.trim().startsWith('deepseek-')
  })

export { DEFAULT_BASE_URL, DEFAULT_MODEL }
