import React, { useEffect, useState } from 'react'
import { t } from '../../i18n'

interface TokenStreamProps {
  text: string
  isStreaming: boolean
}

export const TokenStream: React.FC<TokenStreamProps> = ({ text, isStreaming }) => {
  const [visibleLength, setVisibleLength] = useState(text.length)

  useEffect(() => {
    if (text.length <= visibleLength) {
      setVisibleLength(text.length)
      return undefined
    }

    const timer = window.setInterval(() => {
      setVisibleLength((current) => Math.min(current + 2, text.length))
    }, 16)

    return () => window.clearInterval(timer)
  }, [text, visibleLength])

  const visibleText = text.slice(0, visibleLength)

  return (
    <div className="min-h-24 rounded-lg border border-nrg-border bg-[var(--nrg-surface-1)] p-4">
      {visibleText ? (
        <p className="whitespace-pre-wrap text-base leading-7 text-nrg-text">
          {visibleText}
          {isStreaming && <span className="ml-1 inline-block h-5 w-2 animate-pulse rounded-sm bg-[var(--nrg-focus)] align-middle" />}
        </p>
      ) : (
        <div className="space-y-2" aria-label={t("auto.components.TokenStream.TokenStream.1")}>
          <div className="h-3 w-11/12 animate-pulse rounded-full bg-[var(--nrg-surface-2)]" />
          <div className="h-3 w-9/12 animate-pulse rounded-full bg-[var(--nrg-surface-2)]" />
          <div className="h-3 w-7/12 animate-pulse rounded-full bg-[var(--nrg-surface-2)]" />
        </div>
      )}
    </div>
  )
}

export default TokenStream
