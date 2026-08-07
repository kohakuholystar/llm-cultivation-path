import type { ProgressState } from './store'

export interface AchievementDef {
  id: string
  name: string
  description: string
  icon: string
  expReward: number
  condition: (progress: ProgressState) => boolean
}

/** 成就定义(约 15-20 个,初版 8 个核心)。 */
export const ACHIEVEMENTS: AchievementDef[] = [
  {
    id: 'first-task',
    name: '初出茅庐',
    description: '完成第一个任务',
    icon: '🌱',
    expReward: 20,
    condition: (p) => p.completedTasks.length >= 1,
  },
  {
    id: 'streak-5',
    name: '连战连捷',
    description: '完成 5 个任务',
    icon: '🔥',
    expReward: 30,
    condition: (p) => p.completedTasks.length >= 5,
  },
  {
    id: 'no-hints-3',
    name: '独立思考',
    description: '不使用提示完成 3 个任务',
    icon: '💡',
    expReward: 40,
    condition: (p) => p.stats.perfectTasks >= 3,
  },
  {
    id: 'sandbox-master',
    name: '沙箱达人',
    description: '累计运行沙箱 10 次',
    icon: '⚙️',
    expReward: 30,
    condition: (p) => p.stats.sandboxRuns >= 10,
  },
  {
    id: 'level-5',
    name: '渐入佳境',
    description: '达到 5 级',
    icon: '⭐',
    expReward: 50,
    condition: (p) => p.level >= 5,
  },
  {
    id: 'level-10',
    name: '登堂入室',
    description: '达到 10 级',
    icon: '🏆',
    expReward: 100,
    condition: (p) => p.level >= 10,
  },
  {
    id: 'half-course',
    name: '行百里者半九十',
    description: '完成 20 个任务(半程)',
    icon: '🎯',
    expReward: 80,
    condition: (p) => p.completedTasks.length >= 20,
  },
  {
    id: 'all-done',
    name: '修成正果',
    description: '完成全部 39 个任务',
    icon: '👑',
    expReward: 200,
    condition: (p) => p.completedTasks.length >= 39,
  },
]

/** 检查并解锁新成就,返回新解锁的列表。 */
export function checkAchievements(progress: ProgressState): AchievementDef[] {
  return ACHIEVEMENTS.filter(
    (a) => !progress.achievements.includes(a.id) && a.condition(progress),
  )
}
