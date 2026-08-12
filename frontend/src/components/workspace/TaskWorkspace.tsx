import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useCourse } from '@/features/course/store'
import { useProgress } from '@/features/progression/store'
import { ACHIEVEMENTS } from '@/features/progression/achievements'
import { DEFAULT_BASE_URL, useAiConfig } from '@/features/aiConfig/store'
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

/** 从全局 DeepSeek 配置构造沙箱 env。联网课程必须由学习者提供 Key。 */
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
  const [lastRunCodeHash, setLastRunCodeHash] = useState<string | undefined>()
  const hasDeepSeekConfig = useAiConfig((s) => {
    const baseUrl = s.baseUrl.trim().replace(/\/+$/, '')
    return Boolean(s.apiKey.trim()) && baseUrl === DEFAULT_BASE_URL && s.model.trim().startsWith('deepseek-')
  })
  const setAiConfigModalOpen = useAiConfig((s) => s.setModalOpen)

  useEffect(() => {
    if (!course) loadCourse()
  }, [course, loadCourse])

  const chapter = course?.chapters.find((c) => c.id === chapterId)
  const task = chapter?.tasks.find((t) => t.id === taskId)
  const step = task?.steps[currentStep]
  const stepId = step?.id
  const stepNeedsNetwork = step?.needsNetwork ?? task?.needsNetwork ?? false
  const sandboxTimeout = step?.sandboxTimeout ?? (stepNeedsNetwork ? 30 : 10)
  const sandboxProfile = step?.sandboxProfile ?? 'core'

  // 首次进入联网任务且未配置自己的 API key 时, 自动弹出强制配置引导。
  useEffect(() => {
    if (!task) return
    if (stepNeedsNetwork && !hasDeepSeekConfig) {
      setAiConfigModalOpen(true)
    }
  }, [taskId, stepId, stepNeedsNetwork, hasDeepSeekConfig, setAiConfigModalOpen])

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
      setLastRunCodeHash(undefined)
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
    if (stepNeedsNetwork && !hasDeepSeekConfig) {
      setOutput({
        stdout: '',
        stderr: '联网课程必须先在右上角 DeepSeek 配置中输入你自己的 API Key。',
        exitCode: -1,
        durationMs: 0,
        timedOut: false,
      })
      setAiConfigModalOpen(true)
      return
    }
    setHasRunOrValidated(true)
    setRunning(true)
    setOutput(undefined)
    try {
      const resp = await api.runSandbox({
        code,
        language: 'python',
        timeout: sandboxTimeout,
        needsNetwork: stepNeedsNetwork,
        env: stepNeedsNetwork ? buildLlmEnv() : undefined,
        sandboxProfile,
      })
      setOutput(resp)
      setLastRunCodeHash(strHash(code))
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
  }, [code, step, task, progress, hasDeepSeekConfig, setAiConfigModalOpen, stepNeedsNetwork, sandboxTimeout, sandboxProfile])

  const handleValidate = useCallback(async () => {
    if (!step || !task) return
    if (stepNeedsNetwork && !hasDeepSeekConfig) {
      setOutput({
        stdout: '',
        stderr: '联网课程必须先在右上角 DeepSeek 配置中输入你自己的 API Key。',
        exitCode: -1,
        durationMs: 0,
        timedOut: false,
      })
      setAiConfigModalOpen(true)
      return
    }
    setHasRunOrValidated(true)
    let sandboxOutput = output
    // 联网步骤必须用当前代码完成一次真实 DeepSeek 运行；其他步骤按规则决定是否先运行。
    const needsCurrentRun = (stepNeedsNetwork || stepNeedsSandboxRun(step)) &&
      (!sandboxOutput || lastRunCodeHash !== strHash(code))
    if (needsCurrentRun) {
      setRunning(true)
      try {
        sandboxOutput = await api.runSandbox({
          code,
          language: 'python',
          timeout: sandboxTimeout,
          needsNetwork: stepNeedsNetwork,
          env: stepNeedsNetwork ? buildLlmEnv() : undefined,
          sandboxProfile,
        })
        setOutput(sandboxOutput)
        setLastRunCodeHash(strHash(code))
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
    if (stepNeedsNetwork && sandboxOutput?.exitCode !== 0) {
      result.allPassed = false
      result.results.push({
        ruleIndex: result.results.length,
        ruleType: 'sandbox_run',
        passed: false,
        blocking: true,
        message: '必须用你的 DeepSeek Key 成功完成真实联网运行',
        details: '请检查 Key、账户余额、模型名和网络后重试。',
      })
    }
    // 已迁移行为测试的步骤以服务端 pytest 为最终判定；未迁移步骤保留现有
    // 页面即时反馈，避免把迁移中的课程误判为失败。
    try {
      const authoritative = await api.validateStep(
        task.id,
        step.id,
        code,
        stepNeedsNetwork ? buildLlmEnv() : undefined,
      )
      result.results.push({
        ruleIndex: result.results.length,
        ruleType: 'unit_test',
        passed: authoritative.passed,
        blocking: true,
        message: authoritative.passed ? '服务端行为测试通过' : '服务端行为测试未通过',
        details: authoritative.output.stdout || authoritative.output.stderr || 'pytest 未返回输出',
      })
      if (!authoritative.passed) result.allPassed = false
    } catch (error) {
      // 409 代表该历史步骤尚未迁移 .test.py，不影响原有即时反馈通关。
      if (!(error instanceof Error) || !error.message.startsWith('409:')) {
        result.allPassed = false
        result.results.push({
          ruleIndex: result.results.length,
          ruleType: 'unit_test',
          passed: false,
          blocking: true,
          message: '服务端行为测试暂时不可用',
          details: error instanceof Error ? error.message : String(error),
        })
      }
    }
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
  }, [code, step, task, output, progress, hintsRevealed, hasDeepSeekConfig, setAiConfigModalOpen, lastRunCodeHash, stepNeedsNetwork, sandboxTimeout, sandboxProfile])

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
          返回学习之路
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
          {stepNeedsNetwork && !hasDeepSeekConfig && (
            <div className="border-b border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
              本任务需要真实 DeepSeek 调用。请先点击右上角齿轮输入你自己的 API Key。
            </div>
          )}
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
