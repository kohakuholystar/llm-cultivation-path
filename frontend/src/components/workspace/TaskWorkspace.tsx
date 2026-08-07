import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useCourse } from '@/features/course/store'
import { useProgress } from '@/features/progression/store'
import { ACHIEVEMENTS } from '@/features/progression/achievements'
import { useAiConfig } from '@/features/aiConfig/store'
import { api } from '@/api/client'
import { validateStep, stepNeedsSandboxRun } from '@/utils/validator'
import { strHash } from '@/utils/hash'
import type { SandboxRunResponse, StepValidationResult } from '@shared/types'
import { TaskHeader } from './TaskHeader'
import { StepProgressBar } from './StepProgressBar'
import { CodeEditor } from './CodeEditor'
import { OutputConsole } from './OutputConsole'
import { InfoPanel } from './InfoPanel'
import { CompletionModal } from './CompletionModal'
import { Button } from '@/components/ui'

const STEP_BASE_EXP = 10

/** 从全局 aiConfig 构造沙箱 env(有 key 才传, 无 key 交后端 fallback .env) */
function buildLlmEnv(): Record<string, string> {
  const { apiKey, baseUrl, model } = useAiConfig.getState()
  const env: Record<string, string> = {}
  if (apiKey.trim()) env.OPENAI_API_KEY = apiKey.trim()
  if (baseUrl.trim()) env.OPENAI_BASE_URL = baseUrl.trim()
  if (model.trim()) env.MODEL_NAME = model.trim()
  return env
}

export function TaskWorkspace() {
  const { chapterId, taskId } = useParams()
  const navigate = useNavigate()
  const course = useCourse((s) => s.course)
  const loadCourse = useCourse((s) => s.loadCourse)
  const progress = useProgress()

  const [currentStep, setCurrentStep] = useState(0)
  const [code, setCode] = useState('')
  const [output, setOutput] = useState<SandboxRunResponse | undefined>()
  const [validation, setValidation] = useState<StepValidationResult | undefined>()
  const [running, setRunning] = useState(false)
  const [showComplete, setShowComplete] = useState(false)
  // 用户是否已点过运行/验证(解锁"完整代码参考"Tab)
  const [hasRunOrValidated, setHasRunOrValidated] = useState(false)
  const [hintsRevealed, setHintsRevealed] = useState(0)

  useEffect(() => {
    if (!course) loadCourse()
  }, [course, loadCourse])

  const chapter = course?.chapters.find((c) => c.id === chapterId)
  const task = chapter?.tasks.find((t) => t.id === taskId)
  const step = task?.steps[currentStep]
  const stepId = step?.id

  // 首次进入需要联网的任务且未配置 API key 时, 自动弹出配置引导
  useEffect(() => {
    if (!task) return
    const { apiKey, configured, setModalOpen } = useAiConfig.getState()
    if (task.needsNetwork && !apiKey.trim() && !configured) {
      setModalOpen(true)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskId])

  // 切换 step 时加载草稿/初始代码
  useEffect(() => {
    if (step) {
      const draft = progress.draftCode[step.id]
      // 草稿绑定了来源 starterCode 指纹: 课程代码改版后旧草稿失效并清除, 直接显示课程代码
      if (draft && draft.srcHash === strHash(step.starterCode)) {
        setCode(draft.code)
      } else {
        if (draft) progress.discardDraft(step.id)
        setCode(step.starterCode)
      }
      setHintsRevealed(progress.revealedHints[step.id]?.length ?? 0)
      setOutput(undefined)
      setValidation(undefined)
      setShowComplete(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stepId])

  // 草稿自动保存(debounce 500ms)
  useEffect(() => {
    if (!stepId) return
    const t = setTimeout(
      () => progress.saveDraft(stepId, code, strHash(step.starterCode)),
      500,
    )
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code, stepId])

  const handleRun = useCallback(async () => {
    if (!step || !task) return
    setHasRunOrValidated(true)
    setRunning(true)
    setOutput(undefined)
    try {
      const resp = await api.runSandbox({
        code,
        language: 'python',
        timeout: task.needsNetwork ? 30 : 10,
        needsNetwork: task.needsNetwork,
        env: task.needsNetwork ? buildLlmEnv() : undefined,
      })
      setOutput(resp)
      progress.recordSandboxRun()
    } catch (e) {
      setOutput({
        stdout: '',
        stderr: String(e),
        exitCode: -1,
        durationMs: 0,
        timedOut: false,
        error: String(e),
      })
    } finally {
      setRunning(false)
    }
  }, [code, step, task, progress])

  const handleValidate = useCallback(async () => {
    if (!step || !task) return
    setHasRunOrValidated(true)
    let sandboxOutput = output
    // 需要沙箱但未运行, 先运行
    if (stepNeedsSandboxRun(step) && !sandboxOutput) {
      setRunning(true)
      try {
        sandboxOutput = await api.runSandbox({
          code,
          language: 'python',
          timeout: task.needsNetwork ? 30 : 10,
          needsNetwork: task.needsNetwork,
          env: task.needsNetwork ? buildLlmEnv() : undefined,
        })
        setOutput(sandboxOutput)
        progress.recordSandboxRun()
      } catch (e) {
        sandboxOutput = {
          stdout: '',
          stderr: String(e),
          exitCode: -1,
          durationMs: 0,
          timedOut: false,
          error: String(e),
        }
        setOutput(sandboxOutput)
      } finally {
        setRunning(false)
      }
    }
    const result = await validateStep({ code, step, sandboxOutput })
    setValidation(result)
    if (result.allPassed) {
      const willCompleteTask = task.steps.every(
        (s) => progress.completedSteps.includes(s.id) || s.id === step.id,
      )
      progress.completeStep(step.id, task.id, STEP_BASE_EXP)
      let taskExp = STEP_BASE_EXP
      if (willCompleteTask && !progress.completedTasks.includes(task.id)) {
        progress.completeTask(task.id, task.expReward, hintsRevealed === 0)
        taskExp += task.expReward
      }
      setShowComplete(true)
      void taskExp
    }
  }, [code, step, task, output, progress, hintsRevealed])

  const handleNext = () => {
    setShowComplete(false)
    progress.clearLastUnlocked()
    if (task && currentStep < task.steps.length - 1) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handleCloseComplete = () => {
    setShowComplete(false)
    progress.clearLastUnlocked()
  }

  const handleRevealHint = () => {
    if (!step) return
    if (hintsRevealed < step.hints.length) {
      progress.revealHint(step.id, hintsRevealed)
      setHintsRevealed(hintsRevealed + 1)
    }
  }

  const handleReset = () => {
    if (step && window.confirm('重置为初始代码?当前草稿会丢失。')) {
      setCode(step.starterCode)
      setOutput(undefined)
      setValidation(undefined)
    }
  }

  if (!course) {
    return <div className="p-8 text-center text-slate-400">加载课程中...</div>
  }
  if (!task || !step) {
    return (
      <div className="p-8 text-center">
        <p className="text-slate-400">任务不存在</p>
        <Button className="mt-4" onClick={() => navigate('/learn')}>
          返回修炼之路
        </Button>
      </div>
    )
  }

  const completedStepIds = task.steps
    .filter((s) => progress.completedSteps.includes(s.id))
    .map((s) => s.id)
  const isTaskComplete = completedStepIds.length === task.steps.length

  return (
    <div className="flex h-[calc(100vh-3.5rem-2rem)] flex-col">
      <TaskHeader
        task={task}
        chapter={chapter}
        completedSteps={completedStepIds.length}
      />
      <StepProgressBar
        task={task}
        currentStep={currentStep}
        completedStepIds={completedStepIds}
        onSelect={setCurrentStep}
      />

      <div className="flex flex-1 overflow-hidden">
        {/* 左 2/3: 编辑器 + 输出 */}
        <div className="flex flex-col" style={{ width: '66%' }}>
          <div className="flex items-center gap-2 border-b border-slate-200 bg-white/70 px-3 py-1.5 backdrop-blur">
            <span className="flex items-center gap-1.5 text-xs font-medium text-slate-600">
              <span className="h-2 w-2 rounded-full bg-brand-500 shadow-[0_0_6px_rgba(14,165,233,0.7)]" />
              main.py
            </span>
            <div className="ml-auto flex gap-1">
              <Button size="sm" variant="secondary" onClick={handleRun} disabled={running}>
                {running ? '运行中...' : '运行'}
              </Button>
              <Button size="sm" onClick={handleValidate} disabled={running}>
                验证
              </Button>
              <Button size="sm" variant="ghost" onClick={handleReset}>
                重置
              </Button>
            </div>
          </div>
          <div className="flex-1 overflow-hidden border-b border-slate-200">
            <CodeEditor value={code} onChange={setCode} />
          </div>
          <div className="h-48 border-t border-slate-700">
            <OutputConsole output={output} validation={validation} running={running} />
          </div>
        </div>

        {/* 右 1/3: 信息面板 */}
        <div
          className="overflow-auto border-l border-slate-200 bg-slate-50/60 p-3"
          style={{ width: '34%' }}
        >
          <InfoPanel
            step={step}
            hintsRevealed={hintsRevealed}
            onRevealHint={handleRevealHint}
            hasRunOrValidated={hasRunOrValidated}
          />
        </div>
      </div>

      <CompletionModal
        open={showComplete}
        expGained={STEP_BASE_EXP + (isTaskComplete ? task.expReward : 0)}
        isTaskComplete={isTaskComplete}
        newAchievements={ACHIEVEMENTS.filter((a) => progress.lastUnlocked.includes(a.id))}
        onNext={handleNext}
        onClose={handleCloseComplete}
      />
    </div>
  )
}
