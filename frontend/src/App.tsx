import { RouterProvider } from 'react-router-dom'
import { router } from '@/router'

/** 应用根组件: 挂载 React Router。 */
export default function App() {
  return <RouterProvider router={router} />
}
