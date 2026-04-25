import fs from 'fs'
import path from 'path'

const ROOT = path.resolve(__dirname, '../../src')
const SCAN_DIRS = ['components', 'views'].map((dir) => path.join(ROOT, dir))
const RAW_COLOR = /#[0-9a-fA-F]{3,8}/
const RAW_PX = /\d+px/
const TEXT_FILE = /\.(ts|tsx|js|jsx|css|old)$/

function walk(dir: string): string[] {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const fullPath = path.join(dir, entry.name)
    return entry.isDirectory() ? walk(fullPath) : [fullPath]
  })
}

function lineFor(content: string, index: number): number {
  return content.slice(0, index).split('\n').length
}

describe('component design-token enforcement', () => {
  it('does not use raw hex colors or raw px values in components or views', () => {
    const violations: string[] = []

    for (const file of SCAN_DIRS.flatMap(walk).filter((candidate) => TEXT_FILE.test(candidate))) {
      const content = fs.readFileSync(file, 'utf8')
      const relPath = path.relative(path.resolve(__dirname, '../..'), file)

      for (const pattern of [RAW_COLOR, RAW_PX]) {
        const match = pattern.exec(content)
        if (match) {
          violations.push(`${relPath}:${lineFor(content, match.index)} contains ${match[0]}`)
        }
      }
    }

    expect(violations).toEqual([])
  })
})
