import { useState, useEffect } from 'react'
import { Modal, Button, Badge } from '@/components/ui'
import { useAiConfig, DEFAULT_BASE_URL, DEFAULT_MODEL } from '@/features/aiConfig/store'

interface AiConfigModalProps {
  open: boolean
  onClose: () => void
}

/** 厂商快捷预设 */
const PRESETS = [
  { name: 'DeepSeek', baseUrl: 'https://api.deepseek.com', model: 'deepseek-v4-pro', desc: '便宜, 推荐' },
  { name: '通义千问', baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1', model: 'qwen-max', desc: '阿里云' },
  { name: 'Moonshot', baseUrl: 'https://api.moonshot.cn/v1', model: 'moonshot-v1-8k', desc: 'Kimi' },
  { name: 'OpenAI', baseUrl: 'https://api.openai.com/v1', model: 'gpt-4o-mini', desc: '需代理' },
] as const

/**
 * 全局 AI 配置弹窗。
 * 学习者填一次 API key / base_url / model, 后续所有任务复用。
 * 不填 key 则 fallback 后端 .env 配置。
 */
export function AiConfigModal({ open, onClose }: AiConfigModalProps) {
  const { apiKey, baseUrl, model, accessCode, setConfig } = useAiConfig()
  const [draftKey, setDraftKey] = useState(apiKey)
  const [draftUrl, setDraftUrl] = useState(baseUrl)
  const [draftModel, setDraftModel] = useState(model)
  const [draftCode, setDraftCode] = useState(accessCode)
  const [showKey, setShowKey] = useState(false)
  const [saved, setSaved] = useState(false)
  const [copied, setCopied] = useState(false)

  // 打开时同步当前值到 draft
  useEffect(() => {
    if (open) {
      setDraftKey(apiKey)
      setDraftUrl(baseUrl)
      setDraftModel(model)
      setDraftCode(accessCode)
      setSaved(false)
    }
  }, [open, apiKey, baseUrl, model, accessCode])

  const handleSave = () => {
    setConfig({ apiKey: draftKey.trim(), baseUrl: draftUrl.trim(), model: draftModel.trim(), accessCode: draftCode.trim() })
    setSaved(true)
    setTimeout(onClose, 800)
  }

  const handlePreset = (p: (typeof PRESETS)[number]) => {
    setDraftUrl(p.baseUrl)
    setDraftModel(p.model)
  }

  const handleCopyKey = () => {
    if (!draftKey.trim()) return
    navigator.clipboard.writeText(draftKey.trim())
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <Modal open={open} onClose={onClose} title="⚙️ AI 配置(全局)">
      <p className="mb-4 text-sm text-slate-500">
        填一次, 所有任务自动复用。配置存在浏览器本地, 不会上传。
        <br />
        {!draftKey.trim() && (
          <span className="text-amber-600">
            未填 API key 时, 将 fallback 到后端 .env 配置。
          </span>
        )}
      </p>

      {/* 厂商预设 */}
      <div className="mb-4">
        <div className="panel-title mb-2">快速选择厂商</div>
        <div className="flex flex-wrap gap-2">
          {PRESETS.map((p) => (
            <button
              key={p.name}
              onClick={() => handlePreset(p)}
              className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
                draftUrl === p.baseUrl
                  ? 'border-brand-300 bg-brand-50 text-brand-700'
                  : 'border-slate-200 bg-white text-slate-600 hover:border-brand-200'
              }`}
            >
              {p.name}
              <span className="ml-1 text-slate-400">· {p.desc}</span>
            </button>
          ))}
        </div>
      </div>

      {/* API Key */}
      <div className="mb-3">
        <div className="mb-1 flex items-center justify-between">
          <label className="panel-title">API Key</label>
          {draftKey.trim() && (
            <button
              onClick={handleCopyKey}
              className="rounded px-2 py-0.5 text-xs text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
            >
              {copied ? '已复制 ✓' : '复制'}
            </button>
          )}
        </div>
        <div className="relative">
          <input
            type={showKey ? 'text' : 'password'}
            value={draftKey}
            onChange={(e) => setDraftKey(e.target.value)}
            placeholder="sk-..."
            className="input w-full pr-16 font-mono"
            autoComplete="off"
            spellCheck={false}
          />
          <button
            onClick={() => setShowKey(!showKey)}
            className="absolute right-2 top-1/2 -translate-y-1/2 rounded px-2 py-0.5 text-xs text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            {showKey ? '隐藏' : '显示'}
          </button>
        </div>
      </div>

      {/* Base URL */}
      <div className="mb-3">
        <label className="panel-title mb-1 block">API 接口地址 (base_url)</label>
        <input
          type="text"
          value={draftUrl}
          onChange={(e) => setDraftUrl(e.target.value)}
          placeholder={DEFAULT_BASE_URL}
          className="input w-full font-mono"
          spellCheck={false}
        />
      </div>

      {/* Model */}
      <div className="mb-4">
        <label className="panel-title mb-1 block">模型名</label>
        <input
          type="text"
          value={draftModel}
          onChange={(e) => setDraftModel(e.target.value)}
          placeholder={DEFAULT_MODEL}
          className="input w-full font-mono"
          spellCheck={false}
        />
        <p className="mt-1 text-xs text-slate-400">
          DeepSeek 推荐 <code className="rounded bg-slate-100 px-1 text-brand-700">deepseek-v4-pro</code>(默认) 或{' '}
          <code className="rounded bg-slate-100 px-1 text-brand-700">deepseek-v4-flash</code>(更快更便宜)
        </p>
      </div>

      {/* 访问口令(服务器版) */}
      <div className="mb-4">
        <label className="panel-title mb-1 block">访问口令(服务器版邀请码)</label>
        <input
          type="text"
          value={draftCode}
          onChange={(e) => setDraftCode(e.target.value)}
          placeholder="本地使用可留空"
          className="input w-full font-mono"
          autoComplete="off"
          spellCheck={false}
        />
        <p className="mt-1 text-xs text-slate-400">
          仅当站点部署在服务器、管理员发放了邀请码时才需要填写
        </p>
      </div>

      <div className="flex items-center justify-between">
        <Badge color={draftKey.trim() ? 'green' : 'amber'}>
          {draftKey.trim() ? '已配置 key' : '将用后端 .env'}
        </Badge>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={onClose}>
            取消
          </Button>
          <Button onClick={handleSave}>{saved ? '已保存 ✓' : '保存'}</Button>
        </div>
      </div>
    </Modal>
  )
}
