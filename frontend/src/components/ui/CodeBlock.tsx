import { useState } from 'react'

interface CodeBlockProps {
  code: string
  language?: string
  title?: string
  className?: string
}

export function CodeBlock({ code, language = 'python', title, className }: CodeBlockProps) {
  const [copied, setCopied] = useState(false)
  const handleCopy = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }
  return (
    <div className={`overflow-hidden rounded-xl border border-slate-700 ${className ?? ''}`}>
      <div className="flex items-center justify-between border-b border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-slate-300">
        <span className="flex items-center gap-2">
          <span className="flex gap-1">
            <i className="h-2 w-2 rounded-full bg-red-400/80" />
            <i className="h-2 w-2 rounded-full bg-exp-400/80" />
            <i className="h-2 w-2 rounded-full bg-brand-400/80" />
          </span>
          {title ?? language}
        </span>
        <button
          onClick={handleCopy}
          className="rounded px-1.5 py-0.5 text-slate-400 transition-colors hover:bg-slate-700 hover:text-white"
        >
          {copied ? '已复制 ✓' : '复制'}
        </button>
      </div>
      <pre className="!my-0 !rounded-none !border-0 bg-slate-900 p-3 text-sm">
        <code>{code}</code>
      </pre>
    </div>
  )
}
