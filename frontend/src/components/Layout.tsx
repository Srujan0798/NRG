import React from 'react'
import { useAuth } from '../hooks/useAuth'
import { LogOutIcon } from './Icons'
import { t } from '../i18n'

interface LayoutProps {
  children: React.ReactNode
}

const TIER_STYLES: Record<number, { label: string; bg: string; text: string }> = {
  1: { label: 'Researcher', bg: 'bg-blue-100', text: 'text-blue-800' },
  2: { label: 'Government', bg: 'bg-green-100', text: 'text-green-800' },
  3: { label: 'Industry', bg: 'bg-purple-100', text: 'text-purple-800' },
};

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, logout } = useAuth()
  const tierStyle = user ? TIER_STYLES[user.tier] ?? TIER_STYLES[0] : null

  return (
    <>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-indigo-600 focus:text-white focus:rounded-lg focus:font-medium"
      >
        {t("auto.components.Layout.1")}</a>
      <div className="min-h-screen flex flex-col">
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <h1 className="text-xl font-bold text-gray-900">
                  {t("auto.components.Layout.2")}</h1>
              </div>

              {user && tierStyle && (
                <div className="flex items-center">
                  <div
                    role="status"
                    aria-label={`User tier: ${tierStyle.label}`}
                    className={`flex items-center px-3 py-1 rounded-full text-sm font-medium ${tierStyle.bg} ${tierStyle.text}`}
                  >
                    {tierStyle.label}
                  </div>
                  <div className="ml-4 flex items-center">
                    <span className="text-sm text-gray-700 mr-3">
                      {user.username}
                    </span>
                    <button
                      onClick={() => void logout()}
                      className="flex items-center text-sm text-gray-500 hover:text-gray-700"
                      aria-label={t("auto.components.Layout.3")}
                    >
                      <LogOutIcon className="w-4 h-4 mr-1" aria-hidden="true" />
                      {t("auto.components.Layout.4")}</button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        <main id="main-content" className="flex-grow">
          {children}
        </main>

        <footer className="bg-white border-t border-gray-200">
          <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center">
              <div className="text-sm text-gray-500">
                {t("auto.components.Layout.5")}</div>
              <div className="flex space-x-6">
                <a href="/privacy" className="text-gray-400 hover:text-gray-500">
                  {t("auto.components.Layout.6")}</a>
                <a href="/terms" className="text-gray-400 hover:text-gray-500">
                  {t("auto.components.Layout.7")}</a>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </>
  )
}

export default Layout