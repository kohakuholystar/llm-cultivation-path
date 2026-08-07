/** 稳定字符串哈希(djb2), 用于给 IDE 草稿绑定来源指纹。 */
export function strHash(s: string): string {
  let h = 5381
  for (let i = 0; i < s.length; i++) {
    h = ((h << 5) + h + s.charCodeAt(i)) | 0
  }
  return String(h)
}
