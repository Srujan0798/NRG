import fs from 'fs'
import path from 'path'

const root = process.cwd()
const evidenceDate = process.env.NRG_EVIDENCE_DATE || new Date().toISOString().slice(0, 10)
const evidenceRoot = path.join(root, 'evidence', evidenceDate, 'ui_ux')
const beforeDir = path.join(evidenceRoot, 'before')
const afterDir = path.join(evidenceRoot, 'after')
const galleryPath = path.join(evidenceRoot, 'GALLERY.md')

await fs.promises.mkdir(beforeDir, { recursive: true })
await fs.promises.mkdir(afterDir, { recursive: true })

const afterFiles = fs.existsSync(afterDir)
  ? fs.readdirSync(afterDir).filter((name) => name.endsWith('.png')).sort()
  : []

const lines = [
  '# NRG UI/UX Gallery',
  '',
  'Generated from `scripts/build_before_after_gallery.mjs`.',
  '',
  '| Screen | Before | After |',
  '|---|---|---|',
]

for (const file of afterFiles) {
  const beforePath = `before/${file}`
  const afterPath = `after/${file}`
  const beforeExists = fs.existsSync(path.join(beforeDir, file))
  lines.push(`| ${file} | ${beforeExists ? `![before](${beforePath})` : 'not captured'} | ![after](${afterPath}) |`)
}

if (afterFiles.length === 0) {
  lines.push('| none | not captured | not captured |')
}

await fs.promises.writeFile(galleryPath, `${lines.join('\n')}\n`, 'utf8')
console.log(galleryPath)
