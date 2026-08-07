import type { Step, StepValidationResult, ValidationResult } from '@shared/types'
import type { ValidateContext } from './types'
import { checkRule, ruleNeedsSandbox } from './rules'

/** 验证一个 step 的所有规则。 */
export async function validateStep(ctx: ValidateContext): Promise<StepValidationResult> {
  const results: ValidationResult[] = []
  for (let i = 0; i < ctx.step.validation.length; i++) {
    const rule = ctx.step.validation[i]
    const r = checkRule(rule, ctx)
    results.push({ ...r, ruleIndex: i })
  }
  const blockingFailed = results.some((r) => !r.passed && r.blocking !== false)
  return {
    stepId: ctx.step.id,
    allPassed: !blockingFailed,
    results,
    sandboxOutput: ctx.sandboxOutput,
  }
}

/** 该 step 是否需要沙箱运行(含 output_contains 等需沙箱规则)。 */
export function stepNeedsSandboxRun(step: Step): boolean {
  return step.validation.some(ruleNeedsSandbox)
}

export { checkRule, ruleNeedsSandbox }
export type { ValidateContext }
