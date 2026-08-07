import { Link } from 'react-router-dom'
import { Button } from '@/components/ui'

export function NotFound() {
  return (
    <div className="mx-auto max-w-md px-4 py-24 text-center">
      <div className="text-gradient-hero text-7xl font-bold">404</div>
      <h1 className="mt-4 text-xl font-bold text-slate-900">页面不存在</h1>
      <p className="mt-2 text-slate-500">这条修炼之路还没开辟,返回首页继续。</p>
      <Link to="/" className="mt-6 inline-block">
        <Button>返回首页</Button>
      </Link>
    </div>
  )
}
