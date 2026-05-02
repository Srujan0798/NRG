import React, { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { X } from 'lucide-react'
import { ForceGraph } from '../ForceGraph'
import { GraphData, GraphNode } from '../../services/queryService'
import { t } from '../../i18n'
import { useFocusTrap } from '../../hooks/useFocusTrap'

interface MobileGraphModalProps {
  data: GraphData
  isOpen: boolean
  onClose: () => void
  onNodeClick?: (node: GraphNode) => void
}

export function MobileGraphModal({
  data,
  isOpen,
  onClose,
  onNodeClick,
}: MobileGraphModalProps) {
  const frameRef = useRef<HTMLDivElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)
  const [frameWidth, setFrameWidth] = useState(360)
  useFocusTrap(panelRef, isOpen, onClose)

  useEffect(() => {
    if (!isOpen) return undefined
    const node = frameRef.current
    if (!node || typeof ResizeObserver === 'undefined') return undefined

    const observer = new ResizeObserver(([entry]) => {
      setFrameWidth(Math.max(320, Math.floor(entry.contentRect.width)))
    })
    observer.observe(node)
    return () => observer.disconnect()
  }, [isOpen])

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          ref={panelRef}
          role="dialog"
          aria-modal="true"
          aria-label={t('auto.components.MobileGraphModal.1')}
          data-testid="mobile-graph-modal"
          className="fixed inset-0 z-50 flex flex-col bg-[var(--nrg-surface)] text-nrg-text"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.18 }}
        >
          <div className="flex min-h-16 items-center justify-between gap-3 border-b border-nrg-border px-4">
            <h2 className="min-w-0 truncate text-base font-semibold">
              {t('auto.components.MobileGraphModal.1')}
            </h2>
            <button
              type="button"
              aria-label={t('auto.components.MobileGraphModal.3')}
              onClick={onClose}
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-nrg-border text-nrg-muted transition hover:text-nrg-text"
            >
              <X size={18} aria-hidden="true" />
            </button>
          </div>

          <div ref={frameRef} className="flex-1 overflow-hidden p-3">
            <ForceGraph
              data={data}
              width={frameWidth}
              height={Math.max(520, window.innerHeight - 120)}
              onNodeClick={onNodeClick}
            />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default MobileGraphModal
