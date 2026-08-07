import { useProgress } from '@/features/progression/store'
import { ACHIEVEMENTS } from '@/features/progression/achievements'
import { Card, Badge } from '@/components/ui'

export function Achievements() {
  const progress = useProgress()
  const unlockedCount = progress.achievements.length

  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="text-3xl font-bold text-slate-900">
        成就<span className="text-gradient-exp">墙</span>
      </h1>
      <p className="mt-2 text-slate-500">
        已解锁 <span className="font-semibold text-exp-600">{unlockedCount}</span>/
        {ACHIEVEMENTS.length}
      </p>

      <div className="mt-6 grid gap-3 sm:grid-cols-2">
        {ACHIEVEMENTS.map((a) => {
          const unlocked = progress.achievements.includes(a.id)
          return (
            <Card
              key={a.id}
              hover={unlocked}
              className={
                unlocked
                  ? 'border-exp-200 bg-gradient-to-br from-exp-50 to-brand-50 shadow-glow-exp'
                  : 'border-slate-200 bg-slate-50/60 opacity-60'
              }
            >
              <div className="flex items-center gap-3">
                <span
                  className={`text-3xl ${unlocked ? 'animate-float drop-shadow-[0_0_10px_rgba(233,151,11,0.5)]' : 'grayscale'}`}
                >
                  {unlocked ? a.icon : '🔒'}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="truncate font-semibold text-slate-900">{a.name}</h3>
                    {unlocked && <Badge color="amber">+{a.expReward}</Badge>}
                  </div>
                  <p className="mt-0.5 text-sm text-slate-500">{a.description}</p>
                </div>
              </div>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
