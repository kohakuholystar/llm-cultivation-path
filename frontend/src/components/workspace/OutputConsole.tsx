import type { SandboxRunResponse, StepValidationResult } from '@shared/types'

interface OutputConsoleProps {
  output?: SandboxRunResponse
  validation?: StepValidationResult
  running?: boolean
}

/** 输出控制台: stdout/stderr + 验证结果(深色终端风)。 */
export function OutputConsole({ output, validation, running }: OutputConsoleProps) {
  return (
    <div className="h-full overflow-auto bg-slate-900 p-3 font-mono text-sm">
      {running && (
        <div className="flex items-center gap-2 text-slate-400">
          <span className="h-2 w-2 animate-pulse rounded-full bg-brand-400 shadow-[0_0_6px_rgba(52,211,153,0.9)]" />
          运行中...
        </div>
      )}

      {output && (
        <div className="mb-3">
          {output.stdout && (
            <pre className="whitespace-pre-wrap !border-0 !bg-transparent !p-0 text-emerald-300">
              {output.stdout}
            </pre>
          )}
          {output.stderr && (
            <>
              {output.stderr.includes('Traceback') && (
                <div className="mb-1 text-xs text-amber-300/90">
                  运行出错:下方红字为 Python traceback,报错里的 main.py 行号对应左侧代码编辑器。
                </div>
              )}
              <pre className="whitespace-pre-wrap !border-0 !bg-transparent !p-0 text-red-300">
                {output.stderr}
              </pre>
            </>
          )}
          {output.timedOut && <div className="text-amber-300">执行超时,已终止</div>}
          {output.error && <div className="text-red-400">错误: {output.error}</div>}
          <div className="mt-1 text-xs text-slate-500">
            退出码 {output.exitCode} · {output.durationMs}ms
          </div>
        </div>
      )}

      {validation && (
        <div className="border-t border-slate-700 pt-2">
          <div
            className={`mb-1 font-semibold ${
              validation.allPassed ? 'text-emerald-400' : 'text-red-400'
            }`}
          >
            {validation.allPassed ? '✓ 验证通过' : '✗ 验证未通过'}
          </div>
          {validation.results.map((r) => (
            <div key={r.ruleIndex} className={r.passed ? 'text-emerald-400' : 'text-red-400'}>
              {r.passed ? '✓' : '✗'} {r.message}
              {r.details && <span className="text-slate-500"> ({r.details})</span>}
            </div>
          ))}
        </div>
      )}

      {!output && !validation && !running && (
        <div className="text-slate-600">点击"运行"执行代码,或"验证"检查通关条件</div>
      )}
    </div>
  )
}
