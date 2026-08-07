import { clsx } from 'clsx'
import type { ReactNode } from 'react'

type BadgeColor = 'gray' | 'green' | 'amber' | 'red' | 'blue' | 'purple'

interface BadgeProps {
  color?: BadgeColor
  children: ReactNode
  className?: string
}

const colorClasses: Record<BadgeColor, string> = {
  gray: 'border-slate-200 bg-slate-100 text-slate-600',
  green: 'border-brand-200 bg-brand-50 text-brand-700',
  amber: 'border-exp-200 bg-exp-50 text-exp-700',
  red: 'border-red-200 bg-red-50 text-red-600',
  blue: 'border-blue-200 bg-blue-50 text-blue-700',
  purple: 'border-accent-200 bg-accent-50 text-accent-700',
}

/** 难度 → Badge 颜色 */
export const difficultyColor: Record<string, BadgeColor> = {
  easy: 'green',
  medium: 'blue',
  hard: 'amber',
  boss: 'red',
}

export function Badge({ color = 'gray', children, className }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium',
        colorClasses[color],
        className,
      )}
    >
      {children}
    </span>
  )
}
