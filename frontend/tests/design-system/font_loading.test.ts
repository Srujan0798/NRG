import fs from 'fs'
import path from 'path'

const FRONTEND_ROOT = path.resolve(__dirname, '../..')

describe('self-hosted font loading', () => {
  it('loads local display and mono fonts without external font CDNs', () => {
    const indexHtml = fs.readFileSync(path.join(FRONTEND_ROOT, 'index.html'), 'utf8')
    const indexCss = fs.readFileSync(path.join(FRONTEND_ROOT, 'src/index.css'), 'utf8')

    expect(indexHtml).not.toContain('rel="preload" href="/fonts/')
    expect(indexCss).toContain("font-family: 'Sohne Display'")
    expect(indexCss).toContain("font-family: 'JetBrains Mono'")
    expect(indexCss).toContain("url('/fonts/SohneDisplay.woff2')")
    expect(indexCss).toContain("url('/fonts/JetBrainsMono-Regular.woff2')")
    expect(indexCss).toContain('font-display: swap')
    expect(`${indexHtml}\n${indexCss}`).not.toMatch(/fonts\.(googleapis|gstatic)\.com/)
  })
})
