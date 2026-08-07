import type { ValidationRule, ValidationResult } from '@shared/types'
import type { ValidateContext } from './types'
import { parsePythonLite } from './astLite'

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/**
 * 智能检测 placeholder(如 "# TODO")是否仍未填写。
 *
 * 规则: 找到所有含 placeholder 的行, 逐行看它的"下一非空行":
 *  - 若下一非空行是有效代码(非注释、非空、非纯占位符 pass/None/.../替换这行) → 视为已填写, 跳过
 *  - 若下一非空行是注释, 或其后没有更多代码(文件尾/全是空行) → 视为未填写
 *
 * 这样"说明性 TODO 注释"(如 # TODO: 配置客户端, 下面紧跟已给好的 client=OpenAI(...))
 * 不会误判, 只有真正等待学习者动手的 TODO 才算未完成。
 */
function hasUnfilledPlaceholder(code: string, placeholder: string): boolean {
  if (!code.includes(placeholder)) return false
  const lines = code.split(/\r?\n/)
  // 纯占位符模式(下一行是这些就算未填)
  const placeholderRe = /^\s*(pass|\.\.\.|None|""|'')\s*(#.*)?$/
  for (let i = 0; i < lines.length; i++) {
    if (!lines[i].includes(placeholder)) continue
    // 找下一"有效代码行": 跳过空行和注释行(注释是说明, 不算填写)
    let j = i + 1
    while (j < lines.length) {
      const t = lines[j].trim()
      if (t === '' || t.startsWith('#')) {
        j++
        continue
      }
      break
    }
    if (j >= lines.length) return true // TODO 后无有效代码 → 未填
    const next = lines[j].trim()
    // 下一有效行是纯占位符 → 未填
    if (placeholderRe.test(next)) return true
    // 下一有效行是代码 → 已填写, 继续
  }
  return false
}

/** 检查单条规则(不含 ruleIndex, 由调用方填)。 */
export function checkRule(rule: ValidationRule, ctx: ValidateContext): ValidationResult {
  const { code, sandboxOutput } = ctx
  const base = { ruleType: rule.type, message: rule.message, blocking: rule.blocking ?? true }

  switch (rule.type) {
    case 'api_call_exists': {
      const count = (code.match(new RegExp(escapeRegex(rule.api), 'g')) || []).length
      const need = rule.minCount ?? 1
      return { ruleIndex: 0, ...base, passed: count >= need, details: `找到 ${count} 处, 需 ${need} 处` }
    }
    case 'placeholder_filled': {
      // 智能检测: placeholder(如 # TODO) 若所在行的下一行紧接有效代码(非空/非注释),
      // 视为"已在该处填写",不判失败。只有 TODO 行后是空行/占位符(pass/None/...)才判未填。
      // 这样"说明性 TODO 注释"(代码已给全)不会误判, 只有真正待填的 TODO 才算未完成。
      const stillHas = hasUnfilledPlaceholder(code, rule.placeholder)
      return { ruleIndex: 0, ...base, passed: !stillHas, details: stillHas ? `代码仍含未完成的 ${rule.placeholder}` : undefined }
    }
    case 'regex_in_code': {
      const re = new RegExp(rule.pattern, rule.flags)
      return { ruleIndex: 0, ...base, passed: re.test(code) }
    }
    case 'output_contains': {
      if (!sandboxOutput) return { ruleIndex: 0, ...base, passed: false, details: '需先运行代码' }
      const cs = rule.caseSensitive ?? true
      const stdout = cs ? sandboxOutput.stdout : sandboxOutput.stdout.toLowerCase()
      const text = cs ? rule.text : rule.text.toLowerCase()
      return { ruleIndex: 0, ...base, passed: stdout.includes(text) }
    }
    case 'output_matches': {
      if (!sandboxOutput) return { ruleIndex: 0, ...base, passed: false, details: '需先运行代码' }
      const re = new RegExp(rule.pattern, rule.flags)
      return { ruleIndex: 0, ...base, passed: re.test(sandboxOutput.stdout) }
    }
    case 'output_equals': {
      if (!sandboxOutput) return { ruleIndex: 0, ...base, passed: false, details: '需先运行代码' }
      let a = sandboxOutput.stdout
      let b = rule.expected
      if (rule.trim ?? true) { a = a.trim(); b = b.trim() }
      if (rule.ignoreCase) { a = a.toLowerCase(); b = b.toLowerCase() }
      return { ruleIndex: 0, ...base, passed: a === b, details: `期望 "${b}", 实际 "${a}"` }
    }
    case 'ast_structure': {
      const nodes = parsePythonLite(code).filter((n) => n.type === rule.astType)
      const matched = rule.name
        ? nodes.filter((n) => n.name === rule.name || n.name?.startsWith(rule.name + '.'))
        : nodes
      const need = rule.minCount ?? 1
      return {
        ruleIndex: 0,
        ...base,
        passed: matched.length >= need,
        details: `${rule.astType}${rule.name ? ` "${rule.name}"` : ''} 找到 ${matched.length}, 需 ${need}`,
      }
    }
    case 'unit_test': {
      if (!sandboxOutput) return { ruleIndex: 0, ...base, passed: false, details: '需先运行测试' }
      return { ruleIndex: 0, ...base, passed: sandboxOutput.exitCode === 0 }
    }
    case 'sandbox_run': {
      if (!sandboxOutput) return { ruleIndex: 0, ...base, passed: false, details: '需先运行代码' }
      let passed = true
      const details: string[] = []
      if (rule.stderrMustBeEmpty && sandboxOutput.stderr) {
        passed = false
        details.push('stderr 非空')
      }
      if (rule.expectedExitCode !== undefined && sandboxOutput.exitCode !== rule.expectedExitCode) {
        passed = false
        details.push(`退出码 ${sandboxOutput.exitCode}, 期望 ${rule.expectedExitCode}`)
      }
      if (rule.expectedStdout !== undefined) {
        // expectedStdout 按正则匹配(如 ".*" 表示任意内容, "你好.*" 匹配含"你好"的输出)
        try {
          const re = new RegExp(rule.expectedStdout)
          if (!re.test(sandboxOutput.stdout)) {
            passed = false
            details.push('stdout 不匹配')
          }
        } catch {
          // 非法正则, 回退到精确比较
          if (sandboxOutput.stdout.trim() !== rule.expectedStdout.trim()) {
            passed = false
            details.push('stdout 不匹配')
          }
        }
      }
      return { ruleIndex: 0, ...base, passed, details: details.join('; ') || undefined }
    }
    default:
      return { ruleIndex: 0, ...base, passed: false, details: '未知规则类型' }
  }
}

/** 判断规则是否需要沙箱输出。 */
export function ruleNeedsSandbox(rule: ValidationRule): boolean {
  return ['output_contains', 'output_matches', 'output_equals', 'unit_test', 'sandbox_run'].includes(
    rule.type,
  )
}
