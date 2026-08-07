import { clsx } from 'clsx'
import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'exp'
type Size = 'sm' | 'md' | 'lg'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  children: ReactNode
}

const variantClasses: Record<Variant, string> = {
  primary:
    'bg-gradient-brand text-white font-semibold shadow-glow-brand hover:brightness-105 active:scale-[0.98]',
  secondary:
    'border border-slate-200 bg-white text-slate-700 shadow-soft hover:border-brand-300 hover:text-brand-700',
  ghost: 'text-slate-500 hover:bg-slate-100 hover:text-slate-800',
  danger:
    'border border-red-200 bg-red-50 text-red-600 hover:bg-red-100 hover:border-red-300',
  exp: 'bg-gradient-exp text-white font-semibold shadow-glow-exp hover:brightness-105 active:scale-[0.98]',
}

const sizeClasses: Record<Size, string> = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-5 py-2.5 text-base',
}

export function Button({
  variant = 'primary',
  size = 'md',
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={clsx(
        'inline-flex items-center justify-center gap-1.5 rounded-lg font-medium transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-50',
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  )
}
