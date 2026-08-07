import { useState } from 'react'
import type { Step } from '@shared/types'
import { Tabs, CodeBlock, Collapse, Badge } from '@/components/ui'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface InfoPanelProps {
  step: Step
  hintsRevealed: number
  onRevealHint: () => void
  /** 用户是否已点过运行/验证(解锁"完整代码参考"Tab) */
  hasRunOrValidated: boolean
}

/** 右侧信息面板: 7 个 Tab(说明/任务清单/提示/样例/术语/技术栈/完整代码参考)。
 *  说明/任务清单/提示/样例/完整代码参考 均按当前 step 切换内容。 */
export function InfoPanel({ step, hintsRevealed, onRevealHint, hasRunOrValidated }: InfoPanelProps) {
  const [active, setActive] = useState('instruction')
  // 数据防御: 手写 task.json 可能漏字段, 缺失时按空数组处理, 显示"暂无"空态而非白屏
  const todoItems = step.todoItems ?? []
  const hints = step.hints ?? []
  const codeSamples = step.codeSamples ?? []
  const terms = step.terms ?? []
  const techStack = step.techStack ?? []
  const solutionCode = step.solutionCode ?? ''
  return (
    <Tabs
      active={active}
      onChange={setActive}
      items={[
        {
          key: 'instruction',
          label: '说明',
          content: (
            <div className="markdown-body max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{step.instruction}</ReactMarkdown>
            </div>
          ),
        },
        {
          key: 'todo',
          label: todoItems.length > 0 ? `任务清单 (${todoItems.length})` : '任务清单',
          content: <TodoTab key={step.id} step={step} />,
        },
        {
          key: 'hints',
          label: `提示 (${hintsRevealed}/${hints.length})`,
          content: <HintsTab step={step} revealed={hintsRevealed} onReveal={onRevealHint} />,
        },
        {
          key: 'samples',
          label: '样例',
          content:
            codeSamples.length > 0 ? (
              <div className="space-y-2">
                {codeSamples.map((s, i) => (
                  <Collapse key={i} title={s.title} defaultOpen={codeSamples.length === 1}>
                    <CodeBlock code={s.code} language={s.language} title={s.description} />
                  </Collapse>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-400">本步骤无代码样例</p>
            ),
        },
        {
          key: 'terms',
          label: '术语',
          content:
            terms.length > 0 ? (
              <div className="space-y-2">
                {terms.map((t) => (
                  <div key={t.name} className="rounded-xl border border-slate-200 bg-slate-50/60 p-2.5">
                    <div className="font-semibold text-brand-700">{t.name}</div>
                    <div className="mt-0.5 text-sm text-slate-600">{t.definition}</div>
                    {t.referenceUrl && (
                      <a
                        href={t.referenceUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-brand-600 hover:underline"
                      >
                        参考 →
                      </a>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-400">本步骤无术语</p>
            ),
        },
        {
          key: 'techStack',
          label: '技术栈',
          content:
            techStack.length > 0 ? (
              <div className="space-y-2.5">
                {techStack.map((t) => (
                  <div key={t.name} className="rounded-xl border border-slate-200 bg-white p-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-semibold text-slate-900">{t.name}</span>
                      {t.category && <Badge color="purple">{t.category}</Badge>}
                      <Badge color="blue">{t.role}</Badge>
                    </div>
                    <div className="mt-1.5 text-sm leading-relaxed text-slate-600">{t.description}</div>
                    {t.installHint && (
                      <div className="mt-2 flex items-center gap-1.5 rounded-lg bg-slate-50 px-2.5 py-1.5 font-mono text-xs text-slate-600">
                        <span className="text-brand-500">$</span>
                        {t.installHint}
                      </div>
                    )}
                    <a
                      href={t.officialUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-2 inline-block text-xs text-brand-600 hover:underline"
                    >
                      📖 官方文档 →
                    </a>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-400">本步骤无技术栈</p>
            ),
        },
        {
          key: 'fullSolution',
          label: '完整代码参考',
          disabled: !hasRunOrValidated,
          disabledHint: '先点一次"运行"或"验证"后解锁参考代码',
          content: hasRunOrValidated ? (
            <div className="space-y-3">
              <div className="rounded-lg border border-exp-200 bg-exp-50 px-3 py-2 text-xs text-exp-700">
                💡 当前步骤「{step.title}」的参考代码,仅供对照学习。切换上方步骤可查看对应参考。
              </div>
              <CodeBlock code={solutionCode} language="python" title={`参考代码 · ${step.title}`} />
            </div>
          ) : (
            <div className="py-8 text-center text-sm text-slate-400">
              🔒 先点一次"运行"或"验证"后,即可查看当前步骤的参考代码
            </div>
          ),
        },
      ]}
    />
  )
}

function HintsTab({
  step,
  revealed,
  onReveal,
}: {
  step: Step
  revealed: number
  onReveal: () => void
}) {
  const hints = step.hints ?? []
  const revealedHints = hints.slice(0, revealed)
  return (
    <div>
      {revealedHints.map((h) => (
        <div key={h.order} className="mb-2 rounded-xl border border-exp-200 bg-exp-50 p-2.5 text-sm">
          <div className="flex items-center gap-2">
            <Badge color="amber">提示 {h.order}</Badge>
          </div>
          <p className="mt-1 text-slate-700">{h.text}</p>
        </div>
      ))}
      {revealed < hints.length ? (
        <button
          onClick={onReveal}
          className="mt-2 inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-soft transition-colors hover:border-exp-300 hover:bg-exp-50"
        >
          再给个提示 ({revealed}/{hints.length})
        </button>
      ) : (
        <p className="text-sm text-slate-400">已展示全部提示</p>
      )}
    </div>
  )
}

/** 任务清单 Tab: 每步一张可勾选的任务卡片, 勾选状态随步骤切换重置(组件内 state, 不持久化)。 */
function TodoTab({ step }: { step: Step }) {
  const [done, setDone] = useState<Set<number>>(new Set())
  const items = step.todoItems ?? []
  if (items.length === 0) {
    return <p className="text-sm text-slate-400">本步骤暂无任务清单</p>
  }
  const toggle = (i: number) => {
    setDone((prev) => {
      const next = new Set(prev)
      if (next.has(i)) next.delete(i)
      else next.add(i)
      return next
    })
  }
  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-xs text-slate-500">
        <span>逐项完成, 全部勾选即本步目标达成</span>
        <span className="font-medium text-brand-600">{done.size}/{items.length}</span>
      </div>
      <div className="space-y-2">
        {items.map((item, i) => {
          const checked = done.has(i)
          return (
            <label
              key={i}
              className={`block rounded-xl border p-2.5 transition-colors ${
                checked ? 'border-brand-200 bg-brand-50/50' : 'border-slate-200 bg-white'
              }`}
            >
              <div className="flex items-start gap-2.5">
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggle(i)}
                  className="mt-0.5 h-4 w-4 shrink-0 cursor-pointer accent-brand-600"
                />
                <div className="min-w-0 flex-1">
                  <div className={`text-sm font-medium ${checked ? 'text-slate-400 line-through' : 'text-slate-800'}`}>
                    {item.title}
                  </div>
                  {item.target && (
                    <div className="mt-1 text-xs text-slate-500">
                      <span className="mr-1 rounded bg-slate-100 px-1 py-0.5 font-mono text-[11px] text-slate-500">改哪里</span>
                      {item.target}
                    </div>
                  )}
                  {item.code && <CodeBlock code={item.code} language="python" className="mt-1.5" />}
                  {item.expect && (
                    <div className="mt-1.5 text-xs text-slate-600">
                      <span className="mr-1 rounded bg-exp-50 px-1 py-0.5 font-mono text-[11px] text-exp-700">预期</span>
                      {item.expect}
                    </div>
                  )}
                </div>
              </div>
            </label>
          )
        })}
      </div>
    </div>
  )
}
