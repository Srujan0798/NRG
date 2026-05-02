import { RefObject, useEffect } from 'react'

const focusableSelector = [
  'a[href]',
  'button:not([disabled])',
  'textarea:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',')

function visibleAndFocusable(element: HTMLElement) {
  return !element.hasAttribute('disabled') && element.getAttribute('aria-hidden') !== 'true'
}

function getFocusableElements(container: HTMLElement): HTMLElement[] {
  return Array.from(container.querySelectorAll<HTMLElement>(focusableSelector)).filter(visibleAndFocusable)
}

export function useFocusTrap(
  containerRef: RefObject<HTMLElement>,
  active: boolean,
  onEscape?: () => void,
) {
  useEffect(() => {
    if (!active) return undefined

    const container = containerRef.current
    if (!container) return undefined

    const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null
    if (!container.hasAttribute('tabindex')) container.setAttribute('tabindex', '-1')

    const first = getFocusableElements(container)[0] || container
    first.focus()

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onEscape?.()
        return
      }

      if (event.key !== 'Tab') return

      const focusable = getFocusableElements(container)
      if (focusable.length === 0) {
        event.preventDefault()
        container.focus()
        return
      }

      const first = focusable[0]
      const last = focusable[focusable.length - 1]

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
        return
      }

      if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      if (previousFocus?.isConnected) previousFocus.focus()
    }
  }, [active, containerRef, onEscape])
}
