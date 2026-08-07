/**
 * 沙箱执行相关类型 —— 前后端共享。
 *
 * 后端 POST /api/sandbox/run 接受 SandboxRunRequest,返回 SandboxRunResponse。
 */
import type { SandboxOutput } from './course'

/** 沙箱执行请求 */
export interface SandboxRunRequest {
  /** 学习者代码(python) */
  code: string
  language: 'python'
  /** 标准输入 */
  stdin?: string
  /** 超时秒数,默认 10 */
  timeout?: number
  /** 环境变量(如 OPENAI_API_KEY,仅在 needsNetwork 时注入) */
  env?: Record<string, string>
  /** 是否需要联网(调 LLM API 等);true 时沙箱开放网络 */
  needsNetwork?: boolean
}

/** 沙箱执行响应(扩展 SandboxOutput) */
export interface SandboxRunResponse extends SandboxOutput {
  /** 输出是否被截断(超过长度上限) */
  truncated?: boolean
  /** 执行错误信息(如沙箱不可用) */
  error?: string
}

/** 沙箱状态(健康检查 /api/health 返回) */
export interface SandboxStatus {
  /** 镜像是否就绪 */
  available: boolean
  /** 镜像名 */
  image: string
  /** 当前并发数 */
  concurrency: number
  /** 最大并发数 */
  maxConcurrency: number
}
