import { clsx } from 'clsx'
import { useEffect, type ReactNode } from 'react'

interface ModalProps {
  open: boolean
  onClose: () => void
  title?: ReactNode
  children: ReactNode
  footer?: ReactNode
  className?: string
}

export function Modal({ open, onClose, title, children, footer, className }: ModalProps) {
  // ESC 关闭
  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onClose])

  if (!open) return null
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm animate-fade-in"
      onMouseDown={(e) => {
        // 只在按下点确实是遮罩本身时才关闭:
        // 若从弹窗内容区拖拽选中文本、松手时落在遮罩上, 不会误触发关闭
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        className={clsx(
          'w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-card animate-scale-in',
          className,
        )}
        onClick={(e) => e.stopPropagation()}
      >
        {title && <h2 className="mb-4 text-lg font-semibold text-slate-900">{title}</h2>}
        <div>{children}</div>
        {footer && <div className="mt-5 flex justify-end gap-2">{footer}</div>}
      </div>
    </div>
  )
}
