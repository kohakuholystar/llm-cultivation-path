/** 轻量 Python 结构检查(不引入完整 AST, 用正则 + 缩进感知覆盖 90% 教学场景)。 */

export interface AstLiteNode {
  type:
    | 'function_def'
    | 'async_function_def'
    | 'class_def'
    | 'import'
    | 'import_from'
    | 'call'
    | 'assign'
  name?: string
  line: number
}

const KEYWORDS = new Set([
  'def', 'class', 'if', 'for', 'while', 'return', 'import', 'from',
  'with', 'try', 'except', 'elif', 'else', 'finally', 'print', 'await',
  'yield', 'lambda', 'assert', 'raise', 'global', 'nonlocal',
])

/** 解析 Python 代码为轻量 AST 节点列表。 */
export function parsePythonLite(code: string): AstLiteNode[] {
  const nodes: AstLiteNode[] = []
  const lines = code.split('\n')
  lines.forEach((line, i) => {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) return

    // async def / def
    let m = trimmed.match(/^(async\s+)?def\s+(\w+)\s*\(/)
    if (m) {
      nodes.push({
        type: m[1] ? 'async_function_def' : 'function_def',
        name: m[2],
        line: i + 1,
      })
      return
    }
    // class
    m = trimmed.match(/^class\s+(\w+)/)
    if (m) {
      nodes.push({ type: 'class_def', name: m[1], line: i + 1 })
      return
    }
    // import
    m = trimmed.match(/^import\s+(\S+)/)
    if (m) {
      nodes.push({ type: 'import', name: m[1].split('.')[0], line: i + 1 })
      return
    }
    // from import
    m = trimmed.match(/^from\s+(\S+)\s+import/)
    if (m) {
      nodes.push({ type: 'import_from', name: m[1], line: i + 1 })
      return
    }
    // 顶层赋值
    m = trimmed.match(/^(\w+)\s*=/)
    if (m && !KEYWORDS.has(m[1])) {
      nodes.push({ type: 'assign', name: m[1], line: i + 1 })
    }
    // 函数调用 xxx.xxx(...) 或 xxx(...)
    const callMatches = [...trimmed.matchAll(/\b(\w+(?:\.\w+)*)\s*\(/g)]
    for (const cm of callMatches) {
      const name = cm[1]
      if (!KEYWORDS.has(name.split('.')[0])) {
        nodes.push({ type: 'call', name, line: i + 1 })
      }
    }
  })
  return nodes
}
