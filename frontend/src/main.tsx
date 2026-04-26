import React from 'react'
import ReactDOM from 'react-dom/client'

const root = ReactDOM.createRoot(document.getElementById('root')!)
const loadStyles = () => import('./index.css')

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
