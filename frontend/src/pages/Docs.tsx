import { useEffect, useRef, useState } from 'react'
import { Badge, CodeBlock } from '@/components/ui'
import { TechReferenceGroup } from '@/components/TechReference'
import { useCourse } from '@/features/course/store'
import { TECH_GROUPS } from '@/data/techKB'

/* ================= 内容区块(纯排版, 无卡片) ================= */

/** 快速开始 · 安装与配置 */
function QuickStartInstall() {
  return (
    <div className="animate-fade-in">
      <DocH2 anchor="install">快速开始</DocH2>
      <DocP>从环境准备到完成第一次 LLM 调用,5 分钟跑通整个项目。</DocP>

      <DocH3>环境要求</DocH3>
      <DocUl items={[
        'Node.js ≥ 20 + pnpm ≥ 9',
        'Python ≥ 3.12',
        'Docker Desktop(代码沙箱,可选)',
        '一个 OpenAI 兼容 API key(推荐 DeepSeek,便宜)',
      ]} />

      <DocH3>1. 安装依赖</DocH3>
      <CodeBlock
        code={'pnpm install                            # 前端依赖\ncd backend && pip install -e ".[dev]"   # 后端依赖\ncp .env.example .env                    # 复制环境变量'}
        language="bash"
      />

      <DocH3>2. 配置 API key</DocH3>
      <DocP>
        在项目根目录 <DocCode>.env</DocCode> 填入:
      </DocP>
      <CodeBlock
        code={'OPENAI_API_KEY=sk-...\nOPENAI_BASE_URL=https://api.deepseek.com\nGENERATOR_MODEL=deepseek-v4-pro'}
        language="bash"
      />
      <DocP small>
        接口完全兼容 OpenAI SDK,改 base_url 即可切换厂商(DeepSeek/通义/Moonshot 都支持)。
        你也可以在学习时从导航栏 ⚙️ 直接配置,不用改文件。
      </DocP>

      <DocH3>3. 启动服务</DocH3>
      <CodeBlock
        code={'pnpm dev:backend   # 后端(端口 4200)\npnpm dev          # 前端(端口 3200, 另开终端)'}
        language="bash"
      />
      <DocP small>
        打开 <DocCode>http://localhost:3200</DocCode> 即可开始。
        (可选) 沙箱镜像: <DocCode>pnpm build:sandbox</DocCode>
      </DocP>

      <DocH3>4. 开始第一课</DocH3>
      <DocP>
        访问 <DocCode>/learn</DocCode> 选章节进入任务:
        左侧写代码,右侧看说明/提示/参考代码,点"验证"通关,获得经验解锁下一关。
      </DocP>
    </div>
  )
}

/** 学习路径 */
function LearningPath() {
  return (
    <div className="animate-fade-in">
      <DocH2 anchor="path">学习路径</DocH2>
      <DocP>8 章 39 任务按难度递进,每章有解锁条件(等级/经验/前置任务)。建议按顺序学习。</DocP>

      <DocH3>难度与经验</DocH3>
      <DocP>任务按难度分级,经验奖励递增:</DocP>
      <div className="mb-5 mt-2 flex flex-wrap gap-2">
        <Badge color="green">easy · 10 exp</Badge>
        <Badge color="blue">medium · 20 exp</Badge>
        <Badge color="amber">hard · 40 exp</Badge>
        <Badge color="red">boss · 80 exp</Badge>
      </div>

      <DocH3>章节递进</DocH3>
      <ol className="mb-5 mt-2 space-y-2 text-base text-slate-600">
        {[
          '第一章 初入江湖 · LLM 基础(5 任务):DeepSeek 接入/多轮对话/流式输出/结构化输出/Token 经济学',
          '第二章 拜入山门 · LangChain 架构(5 任务):LCEL 管道/提示词模板/输出解析器/对话记忆/链路由',
          '第三章 秘境探宝 · RAG 检索增强(5 任务):文档加载切分/Embedding 入库/检索重排/RAG 链/评估',
          '第四章 炼器宗师 · Agent 智能体(5 任务):自定义工具/手写 ReAct/AgentExecutor/结构化工具/记忆与人机协同',
          '第五章 内功心法 · Harness 工程(5 任务):核心循环/上下文窗口/错误韧性/可观测/插件化',
          '第六章 分身之术 · 多 Agent 协作(4 任务):消息总线/Supervisor 编排/辩论评审/CrewAI 团队',
          '第七章 袖里乾坤 · 自建小模型(5 任务):Tokenizer/手写 Transformer/训练循环/微调蒸馏/量化部署',
          '第八章 渡劫飞升 · 毕业设计(5 任务):需求架构/核心 RAG/Agent 决策层/Docker 部署/验收上线',
        ].map((t, i) => (
          <li key={i} className="flex gap-3">
            <span className="font-semibold text-slate-400">{i + 1}.</span>
            <span>{t}</span>
          </li>
        ))}
      </ol>

      <DocH3>学习建议</DocH3>
      <DocUl items={[
        '按章节顺序学习,基础不牢不跳关',
        '先自己写代码,再看提示/参考代码(参考代码运行后解锁)',
        '卡住时点"提示"(免费,不扣经验)',
        '通关后回顾"技术栈"Tab,理解每个技术的来龙去脉',
      ]} />
    </div>
  )
}

/** FAQ 常见问题 */
function FaqBlock() {
  const faqs = [
    { q: '需要什么基础?', a: '会 Python 基础语法即可。课程从第一次 LLM API 调用开始,循序渐进到 Agent、RAG、甚至自建小模型。' },
    { q: '需要配置什么?', a: '一个 OpenAI 兼容 API key(支持 DeepSeek/通义/Moonshot 等)。代码执行沙箱需要 Docker(可选,没有则部分任务降级为前端验证)。' },
    { q: '前端后端端口分别是多少?', a: '前端 3200、后端 4200。在 vite.config.ts(server.port+proxy) 与 backend/app/config.py(backend_port) 配置,.env 可覆盖。' },
    { q: '进度会丢失吗?', a: '不会。进度存在浏览器 localStorage,无需登录。Profile 页支持导出/导入进度 JSON,方便迁移设备。' },
    { q: '课程内容是谁写的?', a: '课程内容由 LLM 生成(项目内置课程生成器),结构化教学,经 Pydantic 校验。每章每任务都有完整的步骤、提示、术语、代码样例和验证规则。' },
    { q: '右侧的"任务清单"是什么?', a: '每步右侧顶部会列出 2~4 条 checklist,把当前步骤该做的事拆成可勾选的小项(比如"补全 API Key 校验""实现指数退避重试")。照着逐条完成、逐条打勾,全部勾上后就可以点"验证"通关——它既是步骤指南,也是自检清单。' },
    { q: '代码会在哪运行?', a: '默认前端智能验证(检查代码结构/API 调用),关键任务可点"运行"调后端 Docker 沙箱真实执行,看真实 stdout/stderr。沙箱隔离网络/只读/资源限制,安全。' },
    { q: '"完整代码参考"为什么点不开?', a: '参考代码默认锁定,先点一次"运行"或"验证"后解锁——鼓励先自己动手写,再对照参考。' },
    { q: '能换别的模型吗?', a: '能。接口完全兼容 OpenAI SDK,改导航栏 ⚙️ 的 base_url + model 即可切换 DeepSeek/通义/Moonshot/OpenAI。课程默认 deepseek-v4-pro(便宜)。' },
    { q: '报错 401 / 429 / 5xx 是什么意思?', a: '先认类别再对症下药:401 = Key 失效或填错(回 ⚙️ 检查是否复制完整/过期);429 = 请求过密被限流或额度用尽(DeepSeek 常见余额不足,去控制台充值);5xx = 服务端自身出错/过载,不是你的问题,重试最有效(s4 教的指数退避就是干这个的);连接失败/超时 = 网络不通或 BASE_URL 打错。课程代码里 except 分支的 type(exc).__name__ 打印的就是这些异常类型。' },
  ]
  return (
    <div className="animate-fade-in">
      <DocH2 anchor="faq">FAQ 常见问题</DocH2>
      <div className="mt-4 space-y-6">
        {faqs.map((f) => (
          <div key={f.q}>
            <h4 className="text-base font-semibold text-slate-900">{f.q}</h4>
            <p className="mt-1.5 text-base leading-relaxed text-slate-600">{f.a}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

/* ================= 排版原子组件(文档风) ================= */

function DocH2({ children, anchor }: { children: React.ReactNode; anchor?: string }) {
  return (
    <h2 id={anchor} data-anchor-id={anchor} className="scroll-mt-20 text-2xl font-bold tracking-tight text-slate-900">
      {children}
    </h2>
  )
}
function DocH3({ children }: { children: React.ReactNode }) {
  return <h3 className="mb-2.5 mt-8 text-lg font-semibold text-slate-900">{children}</h3>
}
function DocP({ children, small }: { children: React.ReactNode; small?: boolean }) {
  return <p className={`mt-1.5 leading-relaxed text-slate-600 ${small ? 'text-xs' : 'text-base'}`}>{children}</p>
}
function DocCode({ children }: { children: React.ReactNode }) {
  return <code className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-sm text-brand-700">{children}</code>
}
function DocUl({ items }: { items: string[] }) {
  return (
    <ul className="mt-2 space-y-2 text-base text-slate-600">
      {items.map((t, i) => (
        <li key={i} className="flex gap-2">
          <span className="mt-2 h-1 w-1 flex-shrink-0 rounded-full bg-slate-400" />
          {t}
        </li>
      ))}
    </ul>
  )
}

/* ================= 菜单配置(三级) ================= */
interface MenuLeaf {
  id: string
  label: string
}
interface MenuSub {
  id: string
  label: string
  children?: MenuLeaf[]
}
interface MenuGroup {
  id: string
  label: string
  items: MenuSub[]
}

const MENU: MenuGroup[] = [
  {
    id: 'start',
    label: '快速开始',
    items: [
      { id: 'install', label: '安装与配置' },
      { id: 'path', label: '学习路径' },
    ],
  },
  {
    id: 'tech',
    label: '技术参考',
    items: TECH_GROUPS.map((g) => ({
      id: `techref:${g.title}`,
      label: g.title,
      children: g.techs.map((t) => ({ id: `techref:${g.title}:${t.name}`, label: t.name })),
    })),
  },
  {
    id: 'help',
    label: '帮助',
    items: [{ id: 'faq', label: 'FAQ 常见问题' }],
  },
]

/* ================= 页面主体 ================= */

/** /docs 文档页: 左侧层级菜单(三级) + 右侧纯内容(Kimi 文档风, 无卡片)。 */
export function Docs() {
  const [selected, setSelected] = useState('install')
  const [activeId, setActiveId] = useState('install')
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set())
  const [collapsedSub, setCollapsedSub] = useState<Set<string>>(new Set())

  // scroll-spy: 右侧滚动时,左侧菜单高亮跟随视口内最靠上的锚点
  useEffect(() => {
    let ticking = false
    const compute = () => {
      const anchors = Array.from(document.querySelectorAll<HTMLElement>('[data-anchor-id]'))
      if (anchors.length === 0) return
      // 判定线: 视口顶部向下 25% 处 —— 内容块顶滚过这条线即视为"正在阅读此块",提前高亮更跟手
      const threshold = Math.round(window.innerHeight * 0.25)
      let current = anchors[0]
      for (const a of anchors) {
        if (a.getBoundingClientRect().top <= threshold) current = a
        else break
      }
      const id = current.dataset.anchorId
      if (id) setActiveId(id)
    }
    const onScroll = () => {
      if (ticking) return
      ticking = true
      requestAnimationFrame(() => {
        ticking = false
        compute()
      })
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    compute() // 切换区块后锚点集合变化,立即重算一次
    return () => window.removeEventListener('scroll', onScroll)
  }, [selected])

  // 左侧菜单跟随: 高亮项滚出 aside 可视区时,自动滚回可视区(60+ 项超出视口高度)
  const asideRef = useRef<HTMLElement | null>(null)
  useEffect(() => {
    const aside = asideRef.current
    if (!aside) return
    const btn = aside.querySelector<HTMLElement>(`[data-menu-id="${activeId}"]`)
    if (!btn) return
    const b = btn.getBoundingClientRect()
    const a = aside.getBoundingClientRect()
    if (b.top < a.top) {
      aside.scrollTop += b.top - a.top - 4
    } else if (b.bottom > a.bottom) {
      aside.scrollTop += b.bottom - a.bottom + 4
    }
  }, [activeId])

  const toggle = (id: string) => {
    setCollapsed((s) => {
      const next = new Set(s)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }
  const toggleSub = (id: string) => {
    setCollapsedSub((s) => {
      const next = new Set(s)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  // 点三级菜单(技术项): 选中 + 滚动到对应技术锚点
  const scrollToken = useRef(0)
  const selectTech = (subId: string, techName: string) => {
    const id = `techref:${subId}:${techName}`
    setSelected(id)
    setActiveId(id)
    const token = ++scrollToken.current
    const anchorId = `tech-${techName.replace(/[^a-zA-Z0-9]/g, '-')}`
    const scrollToAnchor = () => {
      if (scrollToken.current !== token) return // 已改点别的技术项,放弃本次滚动
      document.getElementById(anchorId)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
    // 课程数据异步加载中: 「在课程中用到」等 usage 区块还没渲染,锚点位置不固定。
    // 等课程加载完成、React 渲染出 usage 区块后再滚动,避免滚动到一半锚点被顶偏。
    const tryScroll = (attempt: number) => {
      if (scrollToken.current !== token) return
      if (!useCourse.getState().course && attempt < 30) {
        setTimeout(() => tryScroll(attempt + 1), 80)
        return
      }
      // 课程数据已就绪(或等待超时): 双 rAF 等本轮渲染提交、布局稳定后再滚动
      requestAnimationFrame(() => requestAnimationFrame(scrollToAnchor))
    }
    tryScroll(0)
  }

  const renderContent = () => {
    // 技术参考主题或技术项: techref:主题名[:技术名]
    if (selected.startsWith('techref:')) {
      const parts = selected.split(':')
      const groupTitle = parts[1]
      // 高亮跟随 activeId(点击与滚动共用),与 selected 解耦避免滚动时重挂内容
      const activeParts = activeId.split(':')
      const highlightTech = activeId.startsWith('techref:') && activeParts.length === 3 ? activeParts[2] : undefined
      return (
        <div className="animate-fade-in">
          <DocH2 anchor={`techref:${groupTitle}`}>{groupTitle}</DocH2>
          <div className="mt-5">
            <TechReferenceGroup groupTitle={groupTitle} highlight={highlightTech} />
          </div>
        </div>
      )
    }
    switch (selected) {
      case 'install':
        return <QuickStartInstall />
      case 'path':
        return <LearningPath />
      case 'faq':
        return <FaqBlock />
      default:
        return <QuickStartInstall />
    }
  }

  return (
    <div className="w-full">
      <div className="flex">
        {/* 左侧层级菜单(贴左, 粘性, 细边线分隔) */}
        <aside ref={asideRef} className="sticky top-14 hidden h-[calc(100vh-3.5rem)] w-60 flex-shrink-0 overflow-y-auto border-r border-slate-200 py-6 pl-4 pr-6 md:block">
          <nav className="space-y-1">
            {MENU.map((group) => {
              const isCollapsed = collapsed.has(group.id)
              return (
                <div key={group.id}>
                  <button
                    onClick={() => toggle(group.id)}
                    className="flex w-full items-center justify-between rounded-md px-2 py-2 text-left text-sm font-semibold text-slate-700 transition-colors hover:text-slate-900"
                  >
                    {group.label}
                    <span className={`text-xs text-slate-400 transition-transform ${isCollapsed ? '' : 'rotate-90'}`}>▶</span>
                  </button>
                  {!isCollapsed && (
                    <div className="mb-2 mt-0.5 space-y-0.5">
                      {group.items.map((item) => {
                        const isTechGroup = item.children && item.children.length > 0
                        const subCollapsed = collapsedSub.has(item.id)
                        return (
                          <div key={item.id}>
                            <button
                              onClick={() => {
                                if (isTechGroup) {
                                  // 点击主题标题 = 选中 + 确保子项展开(此前被折叠则恢复),便于接着点具体技术
                                  setCollapsedSub((s) => {
                                    if (!s.has(item.id)) return s
                                    const next = new Set(s)
                                    next.delete(item.id)
                                    return next
                                  })
                                  setSelected(item.id) // 选中也显示该主题
                                } else {
                                  setSelected(item.id)
                                }
                                setActiveId(item.id)
                              }}
                              data-menu-id={item.id}
                              className={`flex w-full items-center justify-between rounded-md border-l-2 py-2 pl-4 pr-3 text-left text-sm transition-colors ${
                                activeId === item.id
                                  ? 'border-brand-500 bg-brand-50 font-medium text-brand-700'
                                  : 'border-transparent text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                              }`}
                            >
                              {item.label}
                              {isTechGroup && (
                                <span
                                  onClick={(e) => {
                                    e.stopPropagation() // 折叠/展开只由箭头触发,不改变选中
                                    toggleSub(item.id)
                                  }}
                                  className={`cursor-pointer text-[10px] text-slate-400 transition-transform ${subCollapsed ? '' : 'rotate-90'}`}
                                >▶</span>
                              )}
                            </button>
                            {/* 三级: 技术项 */}
                            {isTechGroup && !subCollapsed && (
                              <div className="mt-0.5 space-y-0.5">
                                {item.children!.map((leaf) => {
                                  const leafActive = activeId === leaf.id
                                  return (
                                    <button
                                      key={leaf.id}
                                      onClick={() => selectTech(item.id.slice('techref:'.length), leaf.label)}
                                      data-menu-id={leaf.id}
                                      className={`w-full rounded-md py-1.5 pl-8 pr-3 text-left text-xs transition-colors ${
                                        leafActive
                                          ? 'bg-brand-50 font-medium text-brand-700'
                                          : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'
                                      }`}
                                    >
                                      {leaf.label}
                                    </button>
                                  )
                                })}
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )
            })}
          </nav>
        </aside>

        {/* 右侧纯内容区(无边框无阴影) */}
        <main className="min-w-0 max-w-screen-2xl flex-1 mx-auto px-6 py-6 md:px-12">
          {/* 移动端菜单切换 */}
          <div className="mb-5 md:hidden">
            <select
              value={selected}
              onChange={(e) => {
                setSelected(e.target.value)
                setActiveId(e.target.value)
              }}
              className="input w-full text-sm"
            >
              {MENU.map((g) => (
                <optgroup key={g.id} label={g.label}>
                  {g.items.map((i) => (
                    <option key={i.id} value={i.id}>{i.label}</option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>
          {renderContent()}
        </main>
      </div>
    </div>
  )
}
