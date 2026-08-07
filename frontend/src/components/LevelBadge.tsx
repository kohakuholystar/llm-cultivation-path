interface LevelBadgeProps {
  level: number
  size?: 'sm' | 'md' | 'lg'
}

const sizeClasses = {
  sm: 'h-7 w-7 text-xs',
  md: 'h-10 w-10 text-sm',
  lg: 'h-14 w-14 text-lg',
}

/** 等级配色: 1-5 铜, 6-10 银, 11-20 金, 21+ 紫(各带发光) */
function colorForLevel(level: number): string {
  if (level >= 21)
    return 'border-accent-400 bg-accent-100 text-accent-700 shadow-[0_0_14px_rgba(127,77,214,0.4)]'
  if (level >= 11)
    return 'border-exp-400 bg-exp-100 text-exp-700 shadow-[0_0_14px_rgba(233,151,11,0.4)]'
  if (level >= 6)
    return 'border-slate-300 bg-slate-100 text-slate-600 shadow-[0_0_10px_rgba(100,116,139,0.25)]'
  return 'border-orange-300 bg-orange-100 text-orange-700 shadow-[0_0_10px_rgba(251,146,60,0.35)]'
}

export function LevelBadge({ level, size = 'md' }: LevelBadgeProps) {
  return (
    <div
      className={`flex flex-shrink-0 items-center justify-center rounded-full border-2 font-bold transition-shadow ${sizeClasses[size]} ${colorForLevel(level)}`}
      title={`等级 ${level}`}
    >
      {level}
    </div>
  )
}
