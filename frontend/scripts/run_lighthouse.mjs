import fs from 'node:fs'
import path from 'node:path'
import { spawn } from 'node:child_process'

const mode = process.argv[2] === 'desktop' ? 'desktop' : 'mobile'
const root = process.cwd()
const repoRoot = path.resolve(root, '..')
const today = new Date().toISOString().slice(0, 10)
const evidenceDir = path.join(repoRoot, 'evidence', today)
const outputPath = path.join(evidenceDir, `lighthouse-${mode}.json`)
const url = 'http://127.0.0.1:4173/app'
const npmConfigCache = path.join(root, '.npm-cache')
const thresholds = mode === 'desktop'
  ? { performance: 0.98, accessibility: 0.70, fcpMs: 800, interactiveMs: 1500 }
  : { performance: 0.95, accessibility: 0.70, fcpMs: 800, interactiveMs: 1500 }

fs.mkdirSync(evidenceDir, { recursive: true })

function run(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: root,
      stdio: options.stdio ?? 'inherit',
      env: { ...process.env, npm_config_cache: npmConfigCache, ...(options.env ?? {}) },
    })

    child.on('error', reject)
    child.on('exit', (code) => {
      if (code === 0) resolve()
      else reject(new Error(`${command} ${args.join(' ')} exited ${code}`))
    })
  })
}

async function waitForPreview(processRef) {
  const started = Date.now()
  while (Date.now() - started < 30000) {
    if (processRef.exitCode !== null) {
      throw new Error('vite preview exited before Lighthouse could connect')
    }
    try {
      const response = await fetch(url)
      if (response.ok) return
    } catch {
      await new Promise((resolve) => setTimeout(resolve, 500))
    }
  }
  throw new Error('Timed out waiting for vite preview on 127.0.0.1:4173')
}

function readScore(report, key) {
  const score = report.categories?.[key]?.score
  return typeof score === 'number' ? score : 0
}

function readAuditMs(report, key) {
  const value = report.audits?.[key]?.numericValue
  return typeof value === 'number' ? value : null
}

await run('npm', ['run', 'build'])

const preview = spawn('npm', ['run', 'preview', '--', '--host', '127.0.0.1', '--port', '4173'], {
  cwd: root,
  stdio: ['ignore', 'pipe', 'pipe'],
  env: { ...process.env, npm_config_cache: npmConfigCache },
})

preview.stdout.on('data', (chunk) => process.stdout.write(chunk))
preview.stderr.on('data', (chunk) => process.stderr.write(chunk))

try {
  await waitForPreview(preview)

  const args = [
    '--yes',
    'lighthouse',
    url,
    '--output=json',
    `--output-path=${outputPath}`,
    '--chrome-flags=--headless --no-sandbox',
    '--only-categories=performance,accessibility',
  ]

  if (mode === 'desktop') {
    args.push('--preset=desktop')
  } else {
    args.push('--form-factor=mobile')
    args.push('--screenEmulation.mobile=true')
  }

  await run('npx', args)

  const report = JSON.parse(fs.readFileSync(outputPath, 'utf8'))
  const performance = readScore(report, 'performance')
  const accessibility = readScore(report, 'accessibility')
  const fcpMs = readAuditMs(report, 'first-contentful-paint')
  const interactiveMs = readAuditMs(report, 'interactive')

  const summary = {
    mode,
    url,
    outputPath,
    performance: Math.round(performance * 100),
    accessibility: Math.round(accessibility * 100),
    firstContentfulPaintMs: fcpMs,
    interactiveMs,
  }
  console.log(JSON.stringify(summary, null, 2))

  const failures = []
  if (performance < thresholds.performance) failures.push(`Performance ${summary.performance} < ${thresholds.performance * 100}`)
  if (accessibility < thresholds.accessibility) failures.push(`Accessibility ${summary.accessibility} < ${thresholds.accessibility * 100}`)
  if (fcpMs !== null && fcpMs > thresholds.fcpMs) failures.push(`FCP ${Math.round(fcpMs)}ms > ${thresholds.fcpMs}ms`)
  if (interactiveMs !== null && interactiveMs > thresholds.interactiveMs) failures.push(`TTI ${Math.round(interactiveMs)}ms > ${thresholds.interactiveMs}ms`)

  if (failures.length > 0) {
    console.error(`Lighthouse ${mode} gate failed: ${failures.join('; ')}`)
    process.exitCode = 1
  }
} finally {
  preview.kill('SIGTERM')
}
