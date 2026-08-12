import { useState, useEffect } from 'react'
import { Modal, Button, Badge } from '@/components/ui'
import { useAiConfig, DEFAULT_BASE_URL, DEFAULT_MODEL } from '@/features/aiConfig/store'
import { api } from '@/api/client'

interface AiConfigModalProps {
  open: boolean
  onClose: () => void
  required?: boolean
  inviteRequired?: boolean
}

/** 云端覆盖层与主树保持相同的 DeepSeek 系统配置门禁。 */
export function AiConfigModal({ open, onClose, required = false, inviteRequired = false }: AiConfigModalProps) {
  const { apiKey, baseUrl, model, accessCode, setConfig } = useAiConfig()
  const [draftKey, setDraftKey] = useState(apiKey)
  const [draftUrl, setDraftUrl] = useState(baseUrl)
  const [draftModel, setDraftModel] = useState(model)
  const [draftAccessCode, setDraftAccessCode] = useState(accessCode)
  const [showKey, setShowKey] = useState(false)
  const [saved, setSaved] = useState(false)
  const [copied, setCopied] = useState(false)
  const [formError, setFormError] = useState('')
  const [verifying, setVerifying] = useState(false)

  useEffect(() => {
    if (open) {
      setDraftKey(apiKey)
      setDraftUrl(DEFAULT_BASE_URL)
      setDraftModel(model)
      setDraftAccessCode(accessCode)
      setSaved(false)
      setFormError('')
    }
  }, [open, apiKey, baseUrl, model, accessCode])

  const handleSave = async () => {
    const apiKey = draftKey.trim()
    const modelName = draftModel.trim()
    const code = draftAccessCode.trim()
    if (!apiKey) {
      setFormError('联网课程必须输入你自己的 DeepSeek API Key。')
      return
    }
    if (!modelName.startsWith('deepseek-')) {
      setFormError('模型名必须是 DeepSeek 模型，例如 deepseek-v4-pro。')
      return
    }
    if (inviteRequired && !code) {
      setFormError('开始使用前必须输入邀请码。')
      return
    }
    if (inviteRequired) {
      setVerifying(true)
      try {
        await api.verifyAccess(code)
      } catch (error) {
        setFormError(error instanceof Error ? error.message : '邀请码验证失败，请重试。')
        return
      } finally {
        setVerifying(false)
      }
    }
    setConfig({ apiKey, baseUrl: DEFAULT_BASE_URL, model: modelName, accessCode: code })
    setSaved(true)
    setTimeout(onClose, 800)
  }

  const handleCopyKey = () => {
    if (!draftKey.trim()) return
    navigator.clipboard.writeText(draftKey.trim())
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      dismissible={!required}
      title={required ? '⚙️ 首次系统配置（开始使用前必填）' : '⚙️ DeepSeek 系统配置'}
    >
      <p className="mb-4 text-sm text-slate-500">
        网站与联网课程会使用你自己的 Key 调用 DeepSeek。Key 只保存在当前浏览器，运行时临时传入沙箱，不保存到服务器。
        <br />
        <span className="text-amber-600">未填写 Key 不能运行或验证联网课程。</span>
      </p>

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
            onChange={(e) => {
              setDraftKey(e.target.value)
              setFormError('')
            }}
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

      <div className="mb-3 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-500">
        接口地址固定为 <code className="font-mono text-brand-700">{draftUrl || DEFAULT_BASE_URL}</code>
      </div>

      <div className="mb-4">
        <label className="panel-title mb-1 block">模型名</label>
        <input
          type="text"
          value={draftModel}
          onChange={(e) => {
            setDraftModel(e.target.value)
            setFormError('')
          }}
          placeholder={DEFAULT_MODEL}
          className="input w-full font-mono"
          spellCheck={false}
        />
        <p className="mt-1 text-xs text-slate-400">
          使用你的 DeepSeek 账户当前可用模型，例如 <code className="rounded bg-slate-100 px-1 text-brand-700">deepseek-v4-pro</code>。
        </p>
      </div>

      {inviteRequired && (
        <div className="mb-4">
          <label className="panel-title mb-1 block">邀请码（必填）</label>
          <input
            type="text"
            value={draftAccessCode}
            onChange={(e) => {
              setDraftAccessCode(e.target.value)
              setFormError('')
            }}
            placeholder="向管理员获取邀请码"
            className="input w-full font-mono"
            autoComplete="off"
            spellCheck={false}
          />
          <p className="mt-1 text-xs text-slate-400">
            当前云端服务器已启用邀请码；未通过验证不能进入网站。
          </p>
        </div>
      )}

      {formError && <p className="mb-3 text-sm text-red-600">{formError}</p>}

      <div className="flex items-center justify-between">
        <Badge color={draftKey.trim() ? 'green' : 'amber'}>
          {draftKey.trim() && (!inviteRequired || draftAccessCode.trim()) ? '待验证系统配置' :
            inviteRequired ? '必须填写 Key 与邀请码' : '必须填写 Key'}
        </Badge>
        <div className="flex gap-2">
          {!required && (
            <Button variant="secondary" onClick={onClose}>
              取消
            </Button>
          )}
          <Button onClick={() => void handleSave()} disabled={verifying}>
            {verifying ? '验证中...' : saved ? '已保存 ✓' : '验证并保存'}
          </Button>
        </div>
      </div>
    </Modal>
  )
}
