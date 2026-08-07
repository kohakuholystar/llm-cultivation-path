import type { Task, Chapter } from '@shared/types'
import { Badge, difficultyColor } from '@/components/ui'

interface TaskHeaderProps {
  task: Task
  chapter?: Chapter
  completedSteps: number
}

export function TaskHeader({ task, chapter, completedSteps }: TaskHeaderProps) {
  return (
    <div className="border-b border-slate-200 bg-white/70 px-4 py-2.5 backdrop-blur">
      <div className="flex items-center gap-1.5 text-xs text-slate-400">
        {chapter && <span>{chapter.title}</span>}
        {chapter && <span className="text-slate-300">›</span>}
        <span className="text-slate-600">{task.title}</span>
      </div>
      <div className="mt-1 flex flex-wrap items-center gap-2">
        <h1 className="text-base font-bold text-slate-900">{task.title}</h1>
        <Badge color={difficultyColor[task.difficulty] ?? 'gray'}>{task.difficulty}</Badge>
        <Badge color="amber">+{task.expReward} exp</Badge>
        <span className="text-xs text-slate-500">
          {completedSteps}/{task.steps.length} 步
        </span>
      </div>
      <p className="mt-0.5 text-xs text-slate-500">{task.learningGoal}</p>
    </div>
  )
}
