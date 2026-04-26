import React, { useEffect } from 'react'
import ReactDOM from 'react-dom/client'
import SkipLink from './components/SkipLink/SkipLink'
import { useReducedMotion } from './hooks/useReducedMotion'
import Hero from './views/Hero'

const root = ReactDOM.createRoot(document.getElementById('root')!)
const loadStyles = () => import('./index.css')

// eslint-disable-next-line react-refresh/only-export-components
const HeroRoute: React.FC<{ Hero: React.ComponentType }> = ({ Hero }) => {
  const reducedMotion = useReducedMotion()

  useEffect(() => {
    document.documentElement.dataset.reducedMotion = reducedMotion ? 'true' : 'false'
    document.title = 'NRG · Ask National Research Graph'
  }, [reducedMotion])

  return (
    <>
      <SkipLink />
      <div data-reduced-motion={reducedMotion ? 'true' : 'false'}>
        <Hero />
      </div>
    </>
  )
}

if (window.location.pathname === '/app') {
  loadStyles().finally(() => root.render(<HeroRoute Hero={Hero} />))
} else {
  Promise.all([
    loadStyles(),
    import('@tanstack/react-query'),
    import('./lib/queryClient'),
    import('./design-system/ThemeProvider'),
    import('./App'),
  ]).then(([, reactQuery, queryClientModule, themeModule, appModule]) => {
    const { QueryClientProvider } = reactQuery
    const { queryClient } = queryClientModule
    const { ThemeProvider } = themeModule
    const App = appModule.default

    root.render(
      <React.StrictMode>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider>
            <App />
          </ThemeProvider>
        </QueryClientProvider>
      </React.StrictMode>
    )
  })
}
