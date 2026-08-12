import { useProgress } from '@/features/progression/store'
import { Card, CardHeader, Button, Badge } from '@/components/ui'
import { LevelBadge } from '@/components/LevelBadge'

export function Profile() {
  const progress = useProgress()

  const handleExport = () => {
    const data = progress.exportData()
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'llmquest-progress.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      try {
        const data = JSON.parse(reader.result as string)
        progress.importData(data)
        alert('进度导入成功')
      } catch {
        alert('导入失败: 文件格式错误')
      }
    }
    reader.readAsText(file)
  }

  const handleReset = () => {
    if (confirm('确定重置所有进度?此操作不可恢复!')) {
      progress.reset()
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <div className="flex items-center gap-4">
        <LevelBadge level={progress.level} size="lg" />
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            Lv.{progress.level} <span className="text-gradient-brand">学习者</span>
          </h1>
          <p className="text-slate-500">
            累计经验 <span className="font-semibold text-exp-600">{progress.totalExp}</span> exp
          </p>
        </div>
      </div>

      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        <Card hover>
          <CardHeader title={String(progress.completedTasks.length)} subtitle="完成任务" />
        </Card>
        <Card hover>
          <CardHeader title={String(progress.completedSteps.length)} subtitle="完成步骤" />
        </Card>
        <Card hover>
          <CardHeader title={String(progress.stats.perfectTasks)} subtitle="无提示通关" />
        </Card>
        <Card hover>
          <CardHeader title={String(progress.stats.sandboxRuns)} subtitle="沙箱运行次数" />
        </Card>
      </div>

      <Card className="mt-8">
        <CardHeader
          title="数据管理"
          subtitle="进度存浏览器 localStorage,可导出备份或迁移设备"
          action={<Badge color="amber">本地优先</Badge>}
        />
        <div className="flex flex-wrap gap-2">
          <Button onClick={handleExport}>导出进度</Button>
          <label className="inline-block">
            <span className="inline-flex cursor-pointer items-center justify-center gap-1.5 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-soft transition-colors hover:border-brand-300 hover:text-brand-700">
              导入进度
            </span>
            <input
              type="file"
              accept=".json"
              onChange={handleImport}
              className="hidden"
            />
          </label>
          <Button variant="danger" onClick={handleReset}>
            重置进度
          </Button>
        </div>
      </Card>

      <Card className="mt-8 border-brand-200 bg-gradient-to-r from-brand-50 to-exp-50">
        <p className="text-sm text-slate-600">
          最后活跃: {new Date(progress.stats.lastActiveAt).toLocaleString('zh-CN')}
        </p>
      </Card>
    </div>
  )
}
