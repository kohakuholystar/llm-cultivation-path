import { createBrowserRouter } from 'react-router-dom'
import { AppLayout } from '@/layouts/AppLayout'
import { Landing } from '@/pages/Landing'
import { About } from '@/pages/About'
import { Docs } from '@/pages/Docs'
import { NotFound } from '@/pages/NotFound'
import { Profile } from '@/pages/Profile'
import { Achievements } from '@/pages/Achievements'
import { CourseMap } from '@/pages/CourseMap'
import { ChapterView } from '@/pages/ChapterView'
import { TaskWorkspace } from '@/components/workspace/TaskWorkspace'

/** 路由表(M4: 工作区核心已接入)。 */
export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <Landing /> },
      { path: 'about', element: <About /> },
      { path: 'docs', element: <Docs /> },
      { path: 'learn', element: <CourseMap /> },
      { path: 'learn/:chapterId', element: <ChapterView /> },
      { path: 'learn/:chapterId/:taskId', element: <TaskWorkspace /> },
      { path: 'profile', element: <Profile /> },
      { path: 'achievements', element: <Achievements /> },
      { path: '*', element: <NotFound /> },
    ],
  },
])
