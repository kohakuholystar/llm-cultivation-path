import { useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useCourse } from '@/features/course/store'
import { useProgress } from '@/features/progression/store'
import { Card, Badge, difficultyColor } from '@/components/ui'

/** 章节详情: 任务列表 + 进度。 */
export function ChapterView() {
  const { chapterId } = useParams()
  const course = useCourse((s) => s.course)
  const loadCourse = useCourse((s) => s.loadCourse)
  const progress = useProgress()

  useEffect(() => {
    if (!course) loadCourse()
  }, [course, loadCourse])

  if (!course) {
    return <div className="p-8 text-center text-slate-400">加载中...</div>
  }
  const chapter = course.chapters.find((c) => c.id === chapterId)
  if (!chapter) {
    return <div className="p-8 text-center text-slate-400">章节不存在</div>
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <Link to="/learn" className="text-sm text-brand-600 hover:underline">
        ‹ 返回修炼之路
      </Link>
      <h1 className="mt-2 text-3xl font-bold text-slate-900">{chapter.title}</h1>
      <p className="mt-1 text-slate-500">{chapter.theme}</p>

      <div className="mt-6 space-y-2.5">
        {chapter.tasks.map((t) => {
          const done = progress.completedTasks.includes(t.id)
          const completedSteps = t.steps.filter((s) =>
            progress.completedSteps.includes(s.id),
          ).length
          return (
            <Link key={t.id} to={`/learn/${chapter.id}/${t.id}`}>
              <Card hover className={done ? 'border-brand-200 bg-brand-50/40' : ''}>
                <div className="flex items-center gap-3">
                  <span className="text-xl">
                    {done ? '✅' : completedSteps > 0 ? '✍️' : '⭕'}
                  </span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-slate-900">{t.title}</span>
                      <Badge color={difficultyColor[t.difficulty] ?? 'gray'}>
                        {t.difficulty}
                      </Badge>
                      <Badge color="amber">+{t.expReward}</Badge>
                    </div>
                    <p className="mt-0.5 text-xs text-slate-500">
                      {completedSteps}/{t.steps.length} 步 · 约 {t.estimatedMinutes} 分钟
                    </p>
                  </div>
                  <span className="text-slate-300">›</span>
                </div>
              </Card>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
