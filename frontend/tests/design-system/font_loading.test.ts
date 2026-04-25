import fs from 'fs'
import path from 'path'

const FRONTEND_ROOT = path.resolve(__dirname, '../..')

describe('self-hosted font loading', () => {
  it('preloads local display and mono fonts without external font CDNs', () => {
    const indexHtml = fs.readFileSync(path.join(FRONTEND_ROOT, 'index.html'), 'utf8')
    const indexCss = fs.readFileSync(path.join(FRONTEND_ROOT, 'src/index.css'), 'utf8')

    expect(indexHtml).toContain('/fonts/SohneDisplay.woff2')
    expect(indexHtml).toContain('/fonts/JetBrainsMono-Regular.woff2')
    expect(indexCss).toContain("font-family: 'Sohne Display'")
    expect(indexCss).toContain("font-family: 'JetBrains Mono'")
    expect(indexCss).toContain('font-display: swap')
    expect(`${indexHtml}\n${indexCss}`).not.toMatch(/fonts\.(googleapis|gstatic)\.com/)
  })
})
