import { clsx } from 'clsx'
import { useEffect, type ReactNode } from 'react'

interface ModalProps {
  open: boolean
  onClose: () => void
  /** 首次系统配置等场景不允许用 ESC 或点击遮罩绕过。 */
  dismissible?: boolean
  title?: ReactNode
  children: ReactNode
  footer?: ReactNode
  className?: string
}

export function Modal({ open, onClose, dismissible = true, title, children, footer, className }: ModalProps) {
  // ESC 关闭
  useEffect(() => {
    if (!open || !dismissible) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onClose, dismissible])

  if (!open) return null
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm animate-fade-in"
      onMouseDown={(e) => {
        // 只在按下点确实是遮罩本身时才关闭:
        // 若从弹窗内容区拖拽选中文本、松手时落在遮罩上, 不会误触发关闭
        if (dismissible && e.target === e.currentTarget) onClose()
      }}
    >
      <div
        className={clsx(
          'w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-card animate-scale-in',
          className,
        )}
        onClick={(e) => e.stopPropagation()}
      >
        {/* 标题栏 + 关闭按钮(X 始终可点, 即使是必填引导也允许先关掉) */}
        <div className="mb-4 flex items-start justify-between">
          {title ? (
            <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
          ) : (
            <span />
          )}
          <button
            onClick={onClose}
            aria-label="关闭"
            className="-mr-1 -mt-1 rounded-lg p-1 text-base leading-none text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
          >
            ✕
          </button>
        </div>
        <div>{children}</div>
        {footer && <div className="mt-5 flex justify-end gap-2">{footer}</div>}
      </div>
    </div>
  )
}
