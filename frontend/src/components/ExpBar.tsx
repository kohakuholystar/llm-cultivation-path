import { useLevelInfo } from '@/features/progression/store'
import { LevelBadge } from './LevelBadge'

/** 顶部经验条: 等级徽章 + 发光进度条 + 经验数值。 */
export function ExpBar() {
  const { level, totalExp, expToNext, progressPercent } = useLevelInfo()
  return (
    <div className="flex items-center gap-3 border-b border-slate-200/80 bg-white/70 px-4 py-1.5 backdrop-blur">
      <LevelBadge level={level} size="sm" />
      <div className="max-w-md flex-1">
        <div className="mb-0.5 flex justify-between text-xs text-slate-500">
          <span className="font-semibold text-brand-600">Lv.{level}</span>
          <span>
            <span className="font-semibold text-exp-600">{totalExp}</span> exp
            {expToNext > 0 && <span className="text-slate-400"> · 距下一级 {expToNext}</span>}
          </span>
        </div>
        <div className="relative h-1.5 overflow-hidden rounded-full bg-slate-200">
          <div
            className="relative h-full rounded-full bg-gradient-to-r from-brand-400 via-brand-500 to-exp-400 shadow-[0_0_8px_rgba(14,165,233,0.5)] transition-all duration-700 ease-out"
            style={{ width: `${progressPercent}%` }}
          >
            {/* 流光扫过 */}
            <span className="absolute inset-0 animate-shimmer bg-gradient-to-r from-transparent via-white/50 to-transparent bg-[length:200%_100%]" />
          </div>
        </div>
      </div>
    </div>
  )
}
