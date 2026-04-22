import { useEffect, useRef, useState } from 'react'

export function useAnimatedCounter(
  endValue: number,
  duration: number = 1600,
  delay: number = 0
): number {
  const [displayValue, setDisplayValue] = useState(0)
  const rafRef = useRef<number | null>(null)
  const startTimeRef = useRef<number | null>(null)
  const startValueRef = useRef(0)

  useEffect(() => {
    let timeoutId: NodeJS.Timeout | null = null

    const startAnimation = () => {
      startValueRef.current = 0
      startTimeRef.current = null

      const animate = (timestamp: number) => {
        if (!startTimeRef.current) startTimeRef.current = timestamp
        const elapsed = timestamp - startTimeRef.current
        const progress = Math.min(elapsed / duration, 1)

        const easeOutQuart = 1 - Math.pow(1 - progress, 4)
        const current = startValueRef.current + (endValue - startValueRef.current) * easeOutQuart

        setDisplayValue(Math.round(current))

        if (progress < 1) {
          rafRef.current = requestAnimationFrame(animate)
        }
      }

      rafRef.current = requestAnimationFrame(animate)
    }

    timeoutId = setTimeout(startAnimation, delay)

    return () => {
      if (timeoutId) clearTimeout(timeoutId)
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [endValue, duration, delay])

  return displayValue
}
