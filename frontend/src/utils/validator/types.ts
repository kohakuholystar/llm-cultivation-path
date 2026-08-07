import type { ValidationRule, ValidationResult, SandboxOutput, Step } from '@shared/types'

export interface ValidateContext {
  code: string
  step: Step
  sandboxOutput?: SandboxOutput
}

export type RuleChecker = (
  rule: ValidationRule,
  ctx: ValidateContext,
) => ValidationResult
