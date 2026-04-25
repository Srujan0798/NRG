import React from 'react'
import { t } from '../../i18n'

interface SkipLinkProps {
  targetId?: string
}

export const SkipLink: React.FC<SkipLinkProps> = ({ targetId = 'main-content' }) => {
  const handleClick = (event: React.MouseEvent<HTMLAnchorElement>) => {
    const target = document.getElementById(targetId)
    if (!target) return

    event.preventDefault()
    target.focus({ preventScroll: true })
    target.scrollIntoView({ block: 'start' })
  }

  return (
    <a
      href={`#${targetId}`}
      onClick={handleClick}
      className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:rounded-lg focus:bg-[var(--nrg-navy)] focus:px-4 focus:py-3 focus:text-sm focus:font-semibold focus:text-white focus:shadow-lg"
    >
      {t('auto.components.Layout.1')}
    </a>
  )
}

export default SkipLink
