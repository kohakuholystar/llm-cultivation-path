import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useCourse } from '@/features/course/store'
import { useProgress } from '@/features/progression/store'
import { Card, Badge } from '@/components/ui'
import { levelFromExp } from '@shared/types'

/** 测试阶段: 强制解锁所有章节(上线前改为 false)。 */
const TEST_UNLOCK_ALL = true

/** 修炼之路: 章节地图, 展示解锁状态与进度。 */
export function CourseMap() {
  const course = useCourse((s) => s.course)
  const loadCourse = useCourse((s) => s.loadCourse)
  const progress = useProgress()

  useEffect(() => {
    if (!course) loadCourse()
  }, [course, loadCourse])

  if (!course) {
    return <div className="p-8 text-center text-slate-400">加载课程中...</div>
  }

  const level = levelFromExp(progress.totalExp)
  const totalTasks = course.chapters.reduce((n, c) => n + c.tasks.length, 0)

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <h1 className="text-3xl font-bold text-slate-900">
        修炼<span className="text-gradient-brand">之路</span>
      </h1>
      <p className="mt-1 text-slate-500">
        完成 {course.chapters.length} 章修炼,从 LLM 基础到自建模型,成为 Agent 工程师
      </p>

      {/* 当前修为面板 */}
      <div className="mt-5 flex flex-wrap items-center gap-x-6 gap-y-2 rounded-2xl border border-brand-200 bg-gradient-to-r from-brand-50 to-exp-50 p-4 text-sm shadow-glow-brand">
        <span className="flex items-center gap-1.5 font-semibold text-brand-700">
          <span className="text-lg">⚡</span> Lv.{level}
        </span>
        <span className="text-exp-600">
          <span className="font-semibold">{progress.totalExp}</span> exp
        </span>
        <span className="text-slate-600">
          已完成 <span className="font-semibold text-slate-900">{progress.completedTasks.length}</span>
          <span className="text-slate-400">/{totalTasks}</span> 任务
        </span>
      </div>

      <div className="mt-8 space-y-3">
        {course.chapters.map((ch, idx) => {
          const completedTasks = ch.tasks.filter((t) =>
            progress.completedTasks.includes(t.id),
          ).length
          const unlocked =
            TEST_UNLOCK_ALL ||
            (level >= ch.unlock.requiredLevel &&
            progress.totalExp >= ch.unlock.requiredExp &&
            ch.unlock.prerequisiteTaskIds.every((id) => progress.completedTasks.includes(id)))
          return (
            <Card
              key={ch.id}
              hover={unlocked}
              className={unlocked ? '' : 'border-slate-200 bg-slate-50/60 opacity-60'}
            >
              <Link to={unlocked ? `/learn/${ch.id}` : '#'} className="block">
                <div className="flex items-center gap-4">
                  <span
                    className={`flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl text-lg font-bold ${
                      unlocked
                        ? 'bg-gradient-brand text-white shadow-glow-brand'
                        : 'bg-slate-200 text-slate-400'
                    }`}
                  >
                    {unlocked ? idx + 1 : '🔒'}
                  </span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-slate-900">{ch.title}</h3>
                      <Badge color={completedTasks === ch.tasks.length ? 'green' : 'gray'}>
                        {completedTasks}/{ch.tasks.length}
                      </Badge>
                    </div>
                    <p className="mt-0.5 text-sm text-slate-500">{ch.theme}</p>
                  </div>
                  {!unlocked && (
                    <span className="text-xs text-slate-400">Lv.{ch.unlock.requiredLevel} 解锁</span>
                  )}
                  {unlocked && <span className="text-brand-400">→</span>}
                </div>
              </Link>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
