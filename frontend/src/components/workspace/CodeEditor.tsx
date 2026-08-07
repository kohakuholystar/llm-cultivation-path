import Editor from '@monaco-editor/react'

interface CodeEditorProps {
  value: string
  onChange: (v: string) => void
  height?: string
}

/** Monaco 代码编辑器封装(language=python, vs-dark 主题)。 */
export function CodeEditor({ value, onChange, height = '100%' }: CodeEditorProps) {
  return (
    <Editor
      height={height}
      language="python"
      theme="vs-dark"
      value={value}
      onChange={(v) => onChange(v ?? '')}
      options={{
        minimap: { enabled: false },
        fontSize: 14,
        tabSize: 4,
        wordWrap: 'on',
        scrollBeyondLastLine: false,
        fixedOverflowWidgets: true,
        automaticLayout: true,
        lineNumbers: 'on',
        contextmenu: true,
        quickSuggestions: true,
      }}
    />
  )
}
