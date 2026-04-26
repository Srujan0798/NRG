import enIN, { generatedCopy } from './en-IN'

type CopyTree = string | string[] | { [key: string]: CopyTree } | Record<string, string>

function lookup(tree: CopyTree, key: string): string | undefined {
  if (typeof tree === 'string' || Array.isArray(tree)) return undefined
  if (Object.keys(tree).includes(key)) {
    const exact = tree[key]
    return typeof exact === 'string' ? exact : undefined
  }

  return key.split('.').reduce<CopyTree | undefined>((current, part) => {
    if (!current || typeof current === 'string' || Array.isArray(current)) return undefined
    return current[part]
  }, tree) as string | undefined
}

export function t(key: string, values?: Record<string, string | number>): string {
  const template = lookup(enIN as CopyTree, key) || generatedCopy[key] || key
  if (!values) return template

  return Object.entries(values).reduce(
    (copy, [token, value]) => copy.replace(new RegExp(`\\{${token}\\}`, 'g'), String(value)),
    template
  )
}

export function countCopyKeys(): number {
  const walk = (value: unknown): number => {
    if (typeof value === 'string') return 1
    if (Array.isArray(value)) return value.filter((item) => typeof item === 'string').length
    if (value && typeof value === 'object') {
      return Object.values(value).reduce((total, item) => total + walk(item), 0)
    }
    return 0
  }

  return walk(enIN)
}

export { enIN }
export * from './en-IN'
