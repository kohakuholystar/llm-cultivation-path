import { Card, CardHeader, Badge } from '@/components/ui'

const techStack = [
  { name: 'React 18 + TypeScript', role: '前端框架' },
  { name: 'Vite', role: '构建工具' },
  { name: 'Monaco Editor', role: '代码编辑器' },
  { name: 'TailwindCSS', role: '样式' },
  { name: 'React Router', role: '路由' },
  { name: 'Zustand', role: '状态管理' },
  { name: 'Python + FastAPI', role: '后端' },
  { name: 'Docker', role: '代码执行沙箱' },
  { name: 'Pydantic', role: '数据校验' },
]

export function About() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="text-3xl font-bold text-slate-900">
        关于<span className="text-gradient-brand">本项目</span>
      </h1>
      <p className="mt-4 leading-relaxed text-slate-600">
        LLM Agent 工程师修炼之路是一个打怪升级式的任务型 LLM 技术栈学习网站。
        目标是让初学者在内置 IDE 环境里,一步步从零掌握 LLM 全技术栈,
        成为能独立开发 Agent 应用的工程师。
      </p>

      <Card className="mt-8">
        <CardHeader title="设计理念" />
        <ul className="space-y-2 text-sm text-slate-600">
          <li>• 任务型学习:每个知识点拆成可完成的任务,带代码验证</li>
          <li>• 打怪升级:等级/经验/成就系统,让学习有进度感</li>
          <li>• 内置 IDE:Monaco 编辑器,带教学注释,所见即所得</li>
          <li>• 真实执行:Docker 沙箱运行代码,看真实输出</li>
          <li>• 本地优先:进度存浏览器,无需登录,数据在你手里</li>
        </ul>
      </Card>

      <h2 className="mt-10 text-xl font-bold text-slate-900">技术栈</h2>
      <div className="mt-4 flex flex-wrap gap-2">
        {techStack.map((t) => (
          <Badge key={t.name} color="gray">
            {t.name} <span className="ml-1 text-slate-400">· {t.role}</span>
          </Badge>
        ))}
      </div>

      <Card className="mt-10 border-brand-200 bg-gradient-to-r from-brand-50 to-exp-50">
        <CardHeader title="致谢" />
        <p className="text-sm text-slate-600">
          课程内容由 LLM 生成,感谢开源社区提供的 LangChain、OpenAI SDK、Chroma、
          FAISS、PyTorch 等优秀工具,让这个学习平台成为可能。
        </p>
      </Card>
    </div>
  )
}
