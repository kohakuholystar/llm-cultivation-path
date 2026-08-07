import { create } from 'zustand'
import type { Course, Chapter, Task } from '@shared/types'
import { api } from '@/api/client'

interface CourseStore {
  course: Course | null
  loading: boolean
  error: string | null
  loadCourse: () => Promise<void>
  getChapter: (id: string) => Chapter | undefined
  getTask: (id: string) => Task | undefined
}

export const useCourse = create<CourseStore>((set, get) => ({
  course: null,
  loading: false,
  error: null,
  loadCourse: async () => {
    if (get().course) return
    set({ loading: true, error: null })
    try {
      const course = await api.getCourse()
      set({ course, loading: false })
    } catch (e) {
      set({ error: e instanceof Error ? e.message : String(e), loading: false })
    }
  },
  getChapter: (id) => get().course?.chapters.find((c) => c.id === id),
  getTask: (id) => {
    for (const c of get().course?.chapters ?? []) {
      for (const t of c.tasks) {
        if (t.id === id) return t
      }
    }
    return undefined
  },
}))
