import { Modal, Button } from '@/components/ui'
import type { AchievementDef } from '@/features/progression/achievements'

interface CompletionModalProps {
  open: boolean
  expGained: number
  isTaskComplete: boolean
  newAchievements?: AchievementDef[]
  onNext: () => void
  onClose: () => void
}

/** 通关弹窗: 经验 + 动画 + 下一步。 */
export function CompletionModal({
  open,
  expGained,
  isTaskComplete,
  newAchievements,
  onNext,
  onClose,
}: CompletionModalProps) {
  return (
    <Modal open={open} onClose={onClose}>
      <div className="text-center">
        <div className="animate-bounce text-5xl drop-shadow-[0_0_16px_rgba(233,151,11,0.5)]">
          {isTaskComplete ? '🏆' : '⭐'}
        </div>
        <h2 className="mt-3 text-xl font-bold text-slate-900">
          {isTaskComplete ? '任务通关!' : '步骤完成!'}
        </h2>
        <div className="text-gradient-exp mt-2 animate-pulse text-3xl font-bold">
          +{expGained} exp
        </div>
        {isTaskComplete && (
          <p className="mt-2 text-sm text-slate-500">恭喜!你完成了整个任务,解锁下一关。</p>
        )}
        {newAchievements && newAchievements.length > 0 && (
          <div className="mt-4 space-y-1.5">
            {newAchievements.map((a) => (
              <div
                key={a.id}
                className="flex items-center justify-center gap-2 rounded-lg bg-amber-50 px-3 py-1.5 text-sm text-amber-800"
              >
                <span>{a.icon}</span>
                <span className="font-medium">解锁成就「{a.name}」</span>
                <span className="text-amber-600">+{a.expReward} exp</span>
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="mt-6 flex justify-center gap-2">
        <Button onClick={onNext}>{isTaskComplete ? '继续' : '下一步'}</Button>
        <Button variant="secondary" onClick={onClose}>
          留在这里
        </Button>
      </div>
    </Modal>
  )
}
