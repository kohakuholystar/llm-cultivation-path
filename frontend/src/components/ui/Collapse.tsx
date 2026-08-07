import { clsx } from 'clsx'
import { useState, type ReactNode } from 'react'

interface CollapseProps {
  title: ReactNode
  children: ReactNode
  defaultOpen?: boolean
  className?: string
}

export function Collapse({ title, children, defaultOpen = false, className }: CollapseProps) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className={clsx('overflow-hidden rounded-xl border border-slate-200 bg-white', className)}>
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-2.5 text-left text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
      >
        <span>{title}</span>
        <span
          className={clsx('text-xs text-slate-400 transition-transform duration-200', open && 'rotate-90 text-brand-500')}
        >
          ▶
        </span>
      </button>
      {open && (
        <div className="animate-fade-in border-t border-slate-100 px-4 py-3">{children}</div>
      )}
    </div>
  )
}
