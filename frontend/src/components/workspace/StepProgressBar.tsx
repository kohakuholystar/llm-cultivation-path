import type { Task } from '@shared/types'

interface StepProgressBarProps {
  task: Task
  currentStep: number
  completedStepIds: string[]
  onSelect: (index: number) => void
}

export function StepProgressBar({
  task,
  currentStep,
  completedStepIds,
  onSelect,
}: StepProgressBarProps) {
  return (
    <div className="flex flex-wrap items-center gap-1.5 border-b border-slate-200 bg-white/60 px-3 py-2">
      {task.steps.map((s, i) => {
        const done = completedStepIds.includes(s.id)
        const current = i === currentStep
        return (
          <button
            key={s.id}
            onClick={() => onSelect(i)}
            className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-medium transition-all duration-200 ${
              current
                ? 'bg-brand-50 text-brand-700 shadow-[inset_0_0_0_1px_rgba(14,165,233,0.35)]'
                : done
                  ? 'text-brand-600 hover:bg-brand-50/60'
                  : 'text-slate-500 hover:bg-slate-100 hover:text-slate-700'
            }`}
          >
            <span
              className={`flex h-4 w-4 items-center justify-center rounded-full text-[10px] ${
                done
                  ? 'bg-gradient-brand text-white'
                  : current
                    ? 'bg-brand-200 text-brand-700'
                    : 'bg-slate-200 text-slate-500'
              }`}
            >
              {done ? '✓' : i + 1}
            </span>
            <span className="hidden sm:inline">{s.title}</span>
          </button>
        )
      })}
    </div>
  )
}
