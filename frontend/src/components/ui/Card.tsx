import { clsx } from 'clsx'
import type { HTMLAttributes, ReactNode } from 'react'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  /** hover 时悬浮抬升 + 边框发光 */
  hover?: boolean
}

export function Card({ className, children, hover = false, ...props }: CardProps) {
  return (
    <div
      className={clsx(
        'rounded-2xl border border-slate-200/80 bg-white p-5 shadow-card transition-all duration-300',
        hover && 'hover:-translate-y-1 hover:border-brand-200 hover:shadow-card-hover',
        className,
      )}
      {...props}
    >
      {children}
    </div>
  )
}

interface CardHeaderProps {
  title: ReactNode
  subtitle?: ReactNode
  action?: ReactNode
  className?: string
}

export function CardHeader({ title, subtitle, action, className }: CardHeaderProps) {
  return (
    <div className={clsx('mb-3 flex items-start justify-between', className)}>
      <div>
        <h3 className="text-base font-semibold text-slate-900">{title}</h3>
        {subtitle && <p className="mt-0.5 text-sm text-slate-500">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}
