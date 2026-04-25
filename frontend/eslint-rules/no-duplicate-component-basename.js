const fs = require('fs')
const path = require('path')

const scanCache = new Map()
const componentExtensions = new Set(['.jsx', '.tsx'])

function findComponentsDir(filename) {
  let current = path.dirname(filename)

  while (current !== path.dirname(current)) {
    const candidate = path.join(current, 'src', 'components')
    if (fs.existsSync(candidate) && fs.statSync(candidate).isDirectory()) {
      return candidate
    }
    current = path.dirname(current)
  }

  return null
}

function isComponentImplementation(filePath) {
  const filename = path.basename(filePath)
  const extension = path.extname(filename)

  if (!componentExtensions.has(extension)) return false
  if (filename.startsWith('__')) return false
  if (filename.endsWith('.test.tsx') || filename.endsWith('.spec.tsx')) return false
  if (filename === 'index.tsx') return false
  if (filePath.includes(`${path.sep}__snapshots__${path.sep}`)) return false

  return true
}

function walk(dir, files = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const entryPath = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      walk(entryPath, files)
    } else {
      files.push(entryPath)
    }
  }

  return files
}

function scanComponents(componentsDir) {
  const cached = scanCache.get(componentsDir)
  if (cached) return cached

  const byBasename = new Map()

  for (const filePath of walk(componentsDir)) {
    if (!isComponentImplementation(filePath)) continue

    const basename = path.basename(filePath, path.extname(filePath))
    const entries = byBasename.get(basename) || []
    entries.push(filePath)
    byBasename.set(basename, entries)
  }

  const duplicates = new Map(
    [...byBasename.entries()].filter(([, entries]) => entries.length > 1)
  )

  scanCache.set(componentsDir, duplicates)
  return duplicates
}

module.exports = {
  meta: {
    type: 'problem',
    docs: {
      description: 'disallow duplicate component implementation basenames under src/components',
    },
    schema: [],
  },
  create(context) {
    return {
      Program(node) {
        const filename = context.getFilename()
        if (filename === '<input>') return

        const componentsDir = findComponentsDir(filename)
        if (!componentsDir) return

        const resolvedFilename = path.resolve(filename)
        if (!resolvedFilename.startsWith(`${componentsDir}${path.sep}`)) return
        if (!isComponentImplementation(resolvedFilename)) return

        const basename = path.basename(resolvedFilename, path.extname(resolvedFilename))
        const duplicateFiles = scanComponents(componentsDir).get(basename)
        if (!duplicateFiles) return

        context.report({
          node,
          message: `Duplicate component basename "${basename}" under src/components: ${duplicateFiles
            .map((filePath) => path.relative(componentsDir, filePath))
            .sort()
            .join(', ')}`,
        })
      },
    }
  },
}
