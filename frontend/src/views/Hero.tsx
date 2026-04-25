import React, { useState } from 'react'
import SearchBar from '../components/SearchBar'
import { ScaleStrip } from '../components/ScaleStrip/ScaleStrip'
import StreamingAnswerPanel from '../components/StreamingAnswerPanel'
import { CitationDrawer } from '../components/CitationDrawer'
import { Citation } from '../services/queryService'
import { t } from '../i18n'

export const Hero: React.FC = () => {
  const [lastQuery, setLastQuery] = useState('')
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null)
  const [isCitationOpen, setIsCitationOpen] = useState(false)

  const handleSubmit = (query: string) => {
    setLastQuery(query)
  }

  const handleCitationClick = (citation: Citation) => {
    setSelectedCitation(citation)
    setIsCitationOpen(true)
  }

  return (
    <main id="main-content" tabIndex={-1} className="nrg-app-canvas min-h-screen px-4 py-8 text-nrg-text sm:px-6 lg:px-8">
      <section className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-5xl flex-col justify-center gap-8">
        <div className="space-y-4">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[var(--nrg-warning)]">
            {t("auto.views.Hero.1")}</p>
          <h1 className="max-w-4xl text-4xl font-bold leading-tight text-nrg-text sm:text-5xl">
            {t("auto.views.Hero.2")}</h1>
          <p className="max-w-2xl text-base leading-7 text-nrg-muted sm:text-lg">
            {t("auto.views.Hero.3")}</p>
        </div>

        <div className="sticky top-0 z-30 rounded-lg bg-[var(--nrg-app-bg)] py-2 sm:static sm:bg-transparent sm:py-0">
          <SearchBar onSubmit={handleSubmit} />
        </div>

        <ScaleStrip />

        <StreamingAnswerPanel query={lastQuery} onCitationClick={handleCitationClick} />
      </section>

      <CitationDrawer
        citation={selectedCitation}
        isOpen={isCitationOpen}
        onClose={() => setIsCitationOpen(false)}
      />
    </main>
  )
}

export default Hero
