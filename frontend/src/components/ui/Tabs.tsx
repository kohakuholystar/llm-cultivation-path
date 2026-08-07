import { clsx } from 'clsx'
import { useState, type ReactNode } from 'react'

export interface TabItem {
  key: string
  label: ReactNode
  content: ReactNode
  /** 禁用(锁定态): 灰显 + 不可点击 + 锁图标 */
  disabled?: boolean
  /** 禁用时的提示文案(title) */
  disabledHint?: string
}

interface TabsProps {
  items: TabItem[]
  defaultActive?: string
  className?: string
  /** 受控模式: 外部控制激活 tab */
  active?: string
  onChange?: (key: string) => void
}

export function Tabs({ items, defaultActive, className, active: controlled, onChange }: TabsProps) {
  const [internal, setInternal] = useState(defaultActive ?? items[0]?.key)
  const active = controlled ?? internal
  const setActive = (k: string) => {
    if (onChange) onChange(k)
    if (controlled === undefined) setInternal(k)
  }
  const activeItem = items.find((i) => i.key === active)
  return (
    <div className={className}>
      <div className="flex flex-wrap gap-1 border-b border-slate-200">
        {items.map((item) => (
          <button
            key={item.key}
            onClick={() => !item.disabled && setActive(item.key)}
            disabled={item.disabled}
            title={item.disabled ? item.disabledHint : undefined}
            className={clsx(
              'relative px-3.5 py-2 text-sm font-medium transition-colors duration-200',
              item.disabled
                ? 'cursor-not-allowed text-slate-300'
                : active === item.key
                  ? 'text-brand-700'
                  : 'text-slate-500 hover:text-slate-800',
            )}
          >
            <span className="inline-flex items-center gap-1">
              {item.label}
              {item.disabled && <span className="text-xs">🔒</span>}
            </span>
            {!item.disabled && active === item.key && (
              <span className="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-gradient-brand shadow-[0_0_8px_rgba(14,165,233,0.5)]" />
            )}
          </button>
        ))}
      </div>
      <div className="pt-3">{activeItem?.content}</div>
    </div>
  )
}
