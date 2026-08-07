import { useMemo, useEffect } from 'react'
import { useCourse } from '@/features/course/store'
import { Badge } from '@/components/ui'
import { TECH_GROUPS, normalizeTechName, type TechInfo } from '@/data/techKB'

/** 技术在课程中用到的地方(按章节聚合) */
interface TechUsage {
  techName: string
  count: number
  chapters: { chTitle: string; steps: string[] }[]
}

/** 扫描课程数据, 聚合每个技术用到的地方 */
export function buildUsageMap(course: ReturnType<typeof useCourse.getState>['course']): Map<string, TechUsage> {
  const map = new Map<string, TechUsage>()
  if (!course) return map
  for (const ch of course.chapters) {
    for (const t of ch.tasks) {
      for (const s of t.steps) {
        for (const ts of s.techStack) {
          const key = normalizeTechName(ts.name)
          if (!key || key === 'none') continue
          if (!map.has(key)) map.set(key, { techName: ts.name, count: 0, chapters: [] })
          const u = map.get(key)!
          u.count += 1
          let chEntry = u.chapters.find((c) => c.chTitle === ch.title)
          if (!chEntry) {
            chEntry = { chTitle: ch.title, steps: [] }
            u.chapters.push(chEntry)
          }
          chEntry.steps.push(`${t.id} · 步骤${s.order}`)
        }
      }
    }
  }
  return map
}

/** 技术锚点 id(用于三级菜单跳转滚动定位) */
function techAnchorId(name: string): string {
  return `tech-${name.replace(/[^a-zA-Z0-9]/g, '-')}`
}

/** 单个技术的详情(纯排版, 带锚点) */
function TechBlock({ tech, usage, highlighted, anchorId }: { tech: TechInfo; usage?: TechUsage; highlighted?: boolean; anchorId?: string }) {
  return (
    <div id={techAnchorId(tech.name)} data-anchor-id={anchorId} className={`-ml-5 -mt-5 mb-8 scroll-mt-20 rounded-lg p-5 ${highlighted ? 'bg-brand-50/60 ring-1 ring-brand-200' : ''}`}>
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-lg font-bold text-slate-900">{tech.name}</h3>
        <Badge color="purple">{tech.category}</Badge>
        {usage && <Badge color="green">用到 {usage.count} 处</Badge>}
      </div>

      <p className="mt-2 leading-relaxed text-slate-600">{tech.description}</p>

      <h4 className="mt-4 mb-1.5 text-sm font-semibold text-slate-900">核心 API 要点</h4>
      <pre className="overflow-x-auto rounded-lg border border-slate-700 bg-slate-900 p-3 text-sm leading-relaxed text-slate-100">
        <code>{tech.apiPoints}</code>
      </pre>

      {tech.installHint && tech.installHint !== 'Python 内置' && (
        <>
          <h4 className="mt-4 mb-1.5 text-sm font-semibold text-slate-900">安装</h4>
          <code className="block rounded-lg bg-slate-100 px-3 py-1.5 font-mono text-sm text-slate-700">
            <span className="mr-1 text-brand-500">$</span>
            {tech.installHint}
          </code>
        </>
      )}

      {usage && usage.chapters.length > 0 && (
        <>
          <h4 className="mt-4 mb-1.5 text-sm font-semibold text-slate-900">在课程中用到</h4>
          <div className="space-y-1 text-sm text-slate-600">
            {usage.chapters.map((c) => (
              <div key={c.chTitle}>
                <span className="font-medium text-slate-700">{c.chTitle}</span>
                <span className="text-slate-400">: {c.steps.join(', ')}</span>
              </div>
            ))}
          </div>
        </>
      )}

      <a
        href={tech.officialUrl}
        target="_blank"
        rel="noreferrer"
        className="mt-3 inline-block text-sm text-brand-600 hover:underline"
      >
        📖 官方文档 →
      </a>
    </div>
  )
}

/** 渲染指定主题分组的技术列表(纯内容, 无内部菜单, 带锚点和高亮) */
export function TechReferenceGroup({ groupTitle, highlight }: { groupTitle: string; highlight?: string }) {
  const course = useCourse((s) => s.course)
  const loadCourse = useCourse((s) => s.loadCourse)

  useEffect(() => {
    if (!course) loadCourse()
  }, [course, loadCourse])

  const usageMap = useMemo(() => buildUsageMap(course), [course])
  const group = TECH_GROUPS.find((g) => g.title === groupTitle)

  if (!group) {
    return <p className="text-sm text-slate-400">主题不存在: {groupTitle}</p>
  }

  return (
    <div>
      {group.techs.map((tech) => {
        const usage = usageMap.get(normalizeTechName(tech.name))
        return (
          <TechBlock
            key={tech.name}
            tech={tech}
            usage={usage}
            highlighted={highlight === tech.name}
            anchorId={`techref:${groupTitle}:${tech.name}`}
          />
        )
      })}
    </div>
  )
}

/** 保留原 TechReference 导出(兼容), 但默认只渲染第一组(避免破坏引用) */
export function TechReference() {
  return <TechReferenceGroup groupTitle={TECH_GROUPS[0].title} />
}
