import { Outlet, Link, NavLink } from 'react-router-dom'
import { ExpBar } from '@/components/ExpBar'
import { AiConfigModal } from '@/components/AiConfigModal'
import { useAiConfig, useHasDeepSeekConfig } from '@/features/aiConfig/store'

const navItems = [
  { to: '/', label: '首页' },
  { to: '/learn', label: '学习之路' },
  { to: '/profile', label: '个人中心' },
  { to: '/achievements', label: '成就' },
  { to: '/about', label: '关于' },
  { to: '/docs', label: '文档' },
]

/** 应用整体布局: 顶部导航 + ExpBar 经验条 + 内容区(Outlet) + 页脚。 */
export function AppLayout() {
  const modalOpen = useAiConfig((s) => s.modalOpen)
  const setModalOpen = useAiConfig((s) => s.setModalOpen)
  const hasSystemConfig = useHasDeepSeekConfig()

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
          <Link to="/" className="group flex items-center gap-2.5 font-semibold">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-brand text-base font-bold text-white shadow-glow-brand transition-transform duration-300 group-hover:rotate-6 group-hover:scale-105">
              修
            </span>
            <span className="hidden bg-gradient-to-r from-brand-600 to-exp-500 bg-clip-text text-transparent sm:inline">
              LLM Agent 工程师学习之路
            </span>
          </Link>
          <nav className="flex items-center gap-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  `rounded-lg px-3 py-1.5 text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-brand-50 text-brand-700 shadow-[inset_0_0_0_1px_rgba(14,165,233,0.25)]'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
            {/* AI 配置齿轮按钮 */}
            <button
              onClick={() => setModalOpen(true)}
              title="AI 配置(全局)"
              className={`relative ml-1 flex h-8 w-8 items-center justify-center rounded-lg transition-all duration-200 ${
                hasSystemConfig
                  ? 'text-brand-600 hover:bg-brand-50'
                  : 'text-amber-500 hover:bg-amber-50'
              }`}
            >
              <span className="text-base">⚙️</span>
              {!hasSystemConfig && (
                <span className="absolute -right-0.5 -top-0.5 h-2 w-2 animate-pulse rounded-full bg-amber-500 shadow-[0_0_6px_rgba(245,158,11,0.8)]" />
              )}
            </button>
          </nav>
        </div>
        <ExpBar />
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 bg-white/70 py-4 text-center text-xs text-slate-400">
        LLM Agent 工程师学习之路 · 打怪升级式 LLM 学习平台 · 本地优先,数据在你手里
      </footer>

      <AiConfigModal
        open={modalOpen || !hasSystemConfig}
        required={!hasSystemConfig}
        onClose={() => {
          if (hasSystemConfig) setModalOpen(false)
        }}
      />
    </div>
  )
}
