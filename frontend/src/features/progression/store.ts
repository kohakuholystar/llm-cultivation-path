import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { checkAchievements } from './achievements'
import {
  PROGRESS_SCHEMA_VERSION,
  DraftCode,
  levelFromExp,
  expFloorForLevel,
  expToNextLevel,
  levelProgressPercent,
} from '@shared/types'

/** 学习者完整进度状态(本地 localStorage 优先)。 */
export interface ProgressState {
  version: number
  userId: string
  level: number
  totalExp: number
  completedSteps: string[]
  completedTasks: string[]
  unlockedChapters: string[]
  currentStepId: string | null
  currentTaskId: string | null
  currentChapterId: string | null
  draftCode: Record<string, DraftCode>
  revealedHints: Record<string, number[]>
  achievements: string[]
  stats: {
    tasksCompleted: number
    perfectTasks: number
    sandboxRuns: number
    totalPlayTimeMs: number
    lastActiveAt: string
  }
  updatedAt: string
}

const defaultProgress: ProgressState = {
  version: PROGRESS_SCHEMA_VERSION,
  userId: 'local',
  level: 1,
  totalExp: 0,
  completedSteps: [],
  completedTasks: [],
  unlockedChapters: [],
  currentStepId: null,
  currentTaskId: null,
  currentChapterId: null,
  draftCode: {},
  revealedHints: {},
  achievements: [],
  stats: {
    tasksCompleted: 0,
    perfectTasks: 0,
    sandboxRuns: 0,
    totalPlayTimeMs: 0,
    lastActiveAt: new Date().toISOString(),
  },
  updatedAt: new Date().toISOString(),
}

interface ProgressStore extends ProgressState {
  /** 最近一次检查中新解锁的成就 id(瞬态, 供通关弹窗展示, 清理由调用方负责)。 */
  lastUnlocked: string[]
  addExp: (amount: number) => void
  completeStep: (stepId: string, taskId: string, exp: number) => void
  completeTask: (taskId: string, exp: number, usedHints: boolean) => void
  revealHint: (stepId: string, hintIndex: number) => void
  saveDraft: (stepId: string, code: string, srcHash: string) => void
  getDraft: (stepId: string) => DraftCode | undefined
  discardDraft: (stepId: string) => void
  setCurrent: (chapterId: string, taskId: string, stepId: string) => void
  recordSandboxRun: () => void
  unlockAchievement: (id: string, expReward: number) => void
  clearLastUnlocked: () => void
  reset: () => void
  exportData: () => ProgressState
  importData: (data: ProgressState) => void
}

const now = () => new Date().toISOString()

export const useProgress = create<ProgressStore>()(
  persist(
    (set, get) => {
      /** 状态变更后自动检查成就; 解锁奖励的 exp 可能连锁触发等级成就, 故循环至无新解锁。 */
      const checkAndUnlock = () => {
        for (;;) {
          const newly = checkAchievements(get())
          if (newly.length === 0) break
          for (const a of newly) {
            get().unlockAchievement(a.id, a.expReward)
            console.info(`[成就] 解锁「${a.name}」 +${a.expReward} exp`)
          }
          set((s) => ({ lastUnlocked: [...s.lastUnlocked, ...newly.map((a) => a.id)] }))
        }
      }

      return {
        ...defaultProgress,
        lastUnlocked: [],

        addExp: (amount) => {
          set((s) => {
            const newExp = Math.max(0, s.totalExp + amount)
            return { totalExp: newExp, level: levelFromExp(newExp), updatedAt: now() }
          })
          checkAndUnlock()
        },

        completeStep: (stepId, taskId, exp) => {
          set((s) => {
            if (s.completedSteps.includes(stepId)) return s
            const newExp = s.totalExp + exp
            return {
              completedSteps: [...s.completedSteps, stepId],
              totalExp: newExp,
              level: levelFromExp(newExp),
              currentStepId: stepId,
              currentTaskId: taskId,
              updatedAt: now(),
            }
          })
          checkAndUnlock()
        },

        completeTask: (taskId, exp, usedHints) => {
          set((s) => {
            if (s.completedTasks.includes(taskId)) return s
            const newExp = s.totalExp + exp
            return {
              completedTasks: [...s.completedTasks, taskId],
              totalExp: newExp,
              level: levelFromExp(newExp),
              stats: {
                ...s.stats,
                tasksCompleted: s.stats.tasksCompleted + 1,
                perfectTasks: s.stats.perfectTasks + (usedHints ? 0 : 1),
                lastActiveAt: now(),
              },
              updatedAt: now(),
            }
          })
          checkAndUnlock()
        },

        revealHint: (stepId, hintIndex) =>
          set((s) => {
            const current = s.revealedHints[stepId] ?? []
            if (current.includes(hintIndex)) return s
            // 不扣 exp(已移除惩罚机制), 仅记录用过的提示(用于"无提示通关"成就判定)
            return {
              revealedHints: { ...s.revealedHints, [stepId]: [...current, hintIndex] },
              updatedAt: now(),
            }
          }),

        saveDraft: (stepId, code, srcHash) =>
          set((s) => ({
            draftCode: { ...s.draftCode, [stepId]: { code, srcHash } },
            updatedAt: now(),
          })),

        getDraft: (stepId) => get().draftCode[stepId],

        discardDraft: (stepId) =>
          set((s) => {
            if (!s.draftCode[stepId]) return s
            const { [stepId]: _, ...rest } = s.draftCode
            return { draftCode: rest, updatedAt: now() }
          }),

        setCurrent: (chapterId, taskId, stepId) =>
          set((s) => ({
            currentChapterId: chapterId,
            currentTaskId: taskId,
            currentStepId: stepId,
            stats: { ...s.stats, lastActiveAt: now() },
            updatedAt: now(),
          })),

        recordSandboxRun: () => {
          set((s) => ({ stats: { ...s.stats, sandboxRuns: s.stats.sandboxRuns + 1 } }))
          checkAndUnlock()
        },

        unlockAchievement: (id, expReward) =>
          set((s) => {
            if (s.achievements.includes(id)) return s
            const newExp = s.totalExp + expReward
            return {
              achievements: [...s.achievements, id],
              totalExp: newExp,
              level: levelFromExp(newExp),
              updatedAt: now(),
            }
          }),

        clearLastUnlocked: () => set({ lastUnlocked: [] }),

        reset: () => set({ ...defaultProgress, lastUnlocked: [], updatedAt: now() }),

        exportData: () => {
          const s = get()
          return {
            version: s.version,
            userId: s.userId,
            level: s.level,
            totalExp: s.totalExp,
            completedSteps: s.completedSteps,
            completedTasks: s.completedTasks,
            unlockedChapters: s.unlockedChapters,
            currentStepId: s.currentStepId,
            currentTaskId: s.currentTaskId,
            currentChapterId: s.currentChapterId,
            draftCode: s.draftCode,
            revealedHints: s.revealedHints,
            achievements: s.achievements,
            stats: s.stats,
            updatedAt: s.updatedAt,
          }
        },

        importData: (data) => set({ ...data, updatedAt: now() }),
      }
    },
    {
      name: 'llmquest:progress:v1',
      version: PROGRESS_SCHEMA_VERSION,
      // 旧版(字符串草稿)升级时全部作废: 草稿可能绑定过期 starterCode(如课程代码改版),
      // 甚至混入用户自测的密钥等敏感内容; 逐字段透传其余进度。
      migrate: (persisted, version) => {
        const p = (persisted ?? {}) as Partial<ProgressState>
        const base = { ...defaultProgress, ...p, version: PROGRESS_SCHEMA_VERSION }
        if (version < PROGRESS_SCHEMA_VERSION) base.draftCode = {}
        return base
      },
      // lastUnlocked 是通关弹窗用的瞬态字段, 不持久化
      partialize: ({ lastUnlocked: _, ...rest }) => rest,
    },
  ),
)

/** 等级/经验派生信息(拆原子选择器, 避免返回新对象致无限重渲染)。 */
export const useLevelInfo = () => {
  const totalExp = useProgress((s) => s.totalExp)
  const level = useProgress((s) => s.level || levelFromExp(s.totalExp))
  return {
    level,
    totalExp,
    expInCurrentLevel: totalExp - expFloorForLevel(level),
    expToNext: expToNextLevel(totalExp),
    progressPercent: levelProgressPercent(totalExp),
  }
}
