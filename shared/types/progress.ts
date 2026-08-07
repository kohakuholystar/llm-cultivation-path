/**
 * 学习者进度 + 成就 + 等级公式。
 *
 * 本地优先: 存浏览器 localStorage(见 frontend 的 progress store,
 * frontend/src/features/progression/store.ts)。
 * 后端预留 /api/progress 接口,数据层抽象好后可接数据库升级多用户。
 *
 * 2026-07-31 对齐: ProgressState / AchievementDef 以前端实际实现为准
 * (frontend/src/features/progression/store.ts + achievements.ts)。
 * 此前 shared 版是早期设计稿(结构化 AchievementCondition、无 stats 等),
 * 与前端真实代码已分叉; 本次重写使 shared 重新成为 single source of truth。
 * 注意: 前端 store 目前仍内联自己的 ProgressState 定义,字段与本文件保持一致。
 */

/** 进度 schema 版本(用于 localStorage 迁移) */
export const PROGRESS_SCHEMA_VERSION = 2

/** IDE 草稿: 绑定来源指纹, 课程 starterCode 更新后旧草稿自动失效 */
export interface DraftCode {
  /** 用户编辑后的代码 */
  code: string
  /** 保存草稿时对应 starterCode 的 strHash 指纹 */
  srcHash: string
}

/** 学习者进度状态 */
export interface ProgressState {
  /** schema 版本,用于迁移 */
  version: number
  /** 本地生成的匿名 ID(预留多用户) */
  userId: string
  /** 当前等级(由 totalExp 经 levelFromExp 派生) */
  level: number
  /** 累计经验 */
  totalExp: number
  /** 已通关的 stepId 数组 */
  completedSteps: string[]
  /** 已通关的 taskId 数组 */
  completedTasks: string[]
  /** 已解锁的 chapterId 数组 */
  unlockedChapters: string[]
  /** 上次做到的 stepId */
  currentStepId: string | null
  /** 上次做到的 taskId */
  currentTaskId: string | null
  /** 上次做到的 chapterId */
  currentChapterId: string | null
  /** stepId -> 草稿代码(绑定 starterCode 指纹, 来源代码更新后旧草稿自动失效) */
  draftCode: Record<string, DraftCode>
  /** stepId -> 已揭示的 hint order 数组 */
  revealedHints: Record<string, number[]>
  /** 已获得的成就 ID */
  achievements: string[]
  /** 学习行为统计(成就判定用) */
  stats: ProgressStats
  /** 最后更新时间(ISO) */
  updatedAt: string
}

/** 学习行为统计 */
export interface ProgressStats {
  /** 累计完成任务数 */
  tasksCompleted: number
  /** 未用提示通关的任务数 */
  perfectTasks: number
  /** 累计沙箱运行次数 */
  sandboxRuns: number
  /** 累计学习时长(毫秒) */
  totalPlayTimeMs: number
  /** 最后活跃时间(ISO) */
  lastActiveAt: string
}

/**
 * 成就定义。
 * condition 为判定函数(以前端 achievements.ts 为准),
 * 不是结构化数据 —— 结构化条件表达能力不足,已被函数取代。
 */
export interface AchievementDef {
  id: string
  name: string
  description: string
  /** emoji 或图标标识 */
  icon: string
  /** 解锁时奖励的经验 */
  expReward: number
  /** 达成判定: 给定进度返回是否解锁 */
  condition: (progress: ProgressState) => boolean
}

/**
 * 等级公式: level = floor(sqrt(totalExp / 100)) + 1
 * - 0 exp → level 1
 * - 100 exp → level 2
 * - 400 exp → level 3
 * - 900 exp → level 4
 *
 * 前端 store 与 CourseMap 直接从本文件 import 使用,勿改签名。
 */
export function levelFromExp(totalExp: number): number {
  return Math.floor(Math.sqrt(totalExp / 100)) + 1
}

/** 达到某等级所需的最低总经验 */
export function expFloorForLevel(level: number): number {
  if (level <= 1) return 0
  return Math.pow(level - 1, 2) * 100
}

/** 距离升到下一级还差多少经验 */
export function expToNextLevel(totalExp: number): number {
  const level = levelFromExp(totalExp)
  return expFloorForLevel(level + 1) - totalExp
}

/** 当前等级在整级中的进度百分比 (0-100) */
export function levelProgressPercent(totalExp: number): number {
  const level = levelFromExp(totalExp)
  const floor = expFloorForLevel(level)
  const ceil = expFloorForLevel(level + 1)
  if (ceil <= floor) return 100
  return Math.min(100, Math.round(((totalExp - floor) / (ceil - floor)) * 100))
}
