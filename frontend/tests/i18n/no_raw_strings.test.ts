import fs from 'fs'
import path from 'path'
import ts from 'typescript'

const FRONTEND_ROOT = path.resolve(__dirname, '../..')
const SOURCE_ROOTS = ['src/components', 'src/views', 'src/pages']
const USER_VISIBLE_ATTRIBUTES = new Set([
  'aria-label',
  'aria-description',
  'placeholder',
  'title',
  'alt',
  'label',
  'description',
  'subtitle',
])

const ALLOWLISTED_FILES = new Set([
  'src/components/Icons.tsx',
  'src/components/__snapshots__/ComponentSnapshots.test.tsx',
])

const ALLOWLISTED_TEXT = new Set([
  'NRG',
  'IIT',
  'IITGN',
  'DPDP',
])

function listTsxFiles(root: string): string[] {
  const absoluteRoot = path.join(FRONTEND_ROOT, root)
  if (!fs.existsSync(absoluteRoot)) return []

  return fs.readdirSync(absoluteRoot, { withFileTypes: true }).flatMap((entry) => {
    const absolutePath = path.join(absoluteRoot, entry.name)
    const relativePath = path.relative(FRONTEND_ROOT, absolutePath)
    if (entry.isDirectory()) return listTsxFiles(relativePath)
    if (!entry.name.endsWith('.tsx')) return []
    if (ALLOWLISTED_FILES.has(relativePath)) return []
    return [absolutePath]
  })
}

function normalizeText(text: string): string {
  return text.replace(/\s+/g, ' ').trim()
}

function isVisibleCopy(text: string): boolean {
  const normalized = normalizeText(text)
  if (normalized.length <= 3) return false
  if (ALLOWLISTED_TEXT.has(normalized)) return false
  if (!/[A-Za-z]/.test(normalized)) return false
  return true
}

function locationOf(sourceFile: ts.SourceFile, node: ts.Node): string {
  const { line, character } = sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile))
  return `${path.relative(FRONTEND_ROOT, sourceFile.fileName)}:${line + 1}:${character + 1}`
}

function scanFile(filePath: string): string[] {
  const sourceText = fs.readFileSync(filePath, 'utf8')
  const sourceFile = ts.createSourceFile(filePath, sourceText, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX)
  const failures: string[] = []

  const visit = (node: ts.Node) => {
    if (ts.isJsxText(node) && isVisibleCopy(node.getText(sourceFile))) {
      failures.push(`${locationOf(sourceFile, node)} raw JSX text "${normalizeText(node.getText(sourceFile))}"`)
    }

    if (ts.isJsxAttribute(node)) {
      const attributeName = node.name.getText(sourceFile)
      if (
        USER_VISIBLE_ATTRIBUTES.has(attributeName) &&
        node.initializer &&
        ts.isStringLiteral(node.initializer) &&
        isVisibleCopy(node.initializer.text)
      ) {
        failures.push(`${locationOf(sourceFile, node)} raw ${attributeName} "${node.initializer.text}"`)
      }
    }

    ts.forEachChild(node, visit)
  }

  visit(sourceFile)
  return failures
}

describe('i18n source discipline', () => {
  it('keeps user-visible JSX copy out of components and views', () => {
    const failures = SOURCE_ROOTS.flatMap(listTsxFiles).flatMap(scanFile)
    expect(failures).toEqual([])
  })
})
