import React from 'react'
import { useAuth } from '../hooks/useAuth'
import { LogOutIcon } from './Icons'

interface LayoutProps {
  children: React.ReactNode
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, logout } = useAuth()

  const getUserTypeLabel = () => {
    if (!user) return ''
    
    switch(user.tier) {
      case 1: return 'Researcher'
      case 2: return 'Government'
      case 3: return 'Industry'
      default: return ''
    }
  }

  const getUserTypeColor = () => {
    if (!user) return 'gray'
    
    switch(user.tier) {
      case 1: return 'blue'
      case 2: return 'green'
      case 3: return 'purple'
      default: return 'gray'
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">
                National Research Intelligence
              </h1>
            </div>
            
            {user && (
              <div className="flex items-center">
                <div className={`flex items-center px-3 py-1 rounded-full text-sm font-medium bg-${getUserTypeColor()}-100 text-${getUserTypeColor()}-800`}>
                  {getUserTypeLabel()}
                </div>
                <div className="ml-4 flex items-center">
                  <span className="text-sm text-gray-700 mr-3">
                    {user.username}
                  </span>
                  <button
                    onClick={() => void logout()}
                    className="flex items-center text-sm text-gray-500 hover:text-gray-700"
                  >
                    <LogOutIcon className="w-4 h-4 mr-1" />
                    Sign out
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>
      
      <main className="flex-grow">
        {children}
      </main>
      
      <footer className="bg-white border-t border-gray-200">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <div className="text-sm text-gray-500">
              © 2026 National Research Intelligence Platform. All rights reserved.
            </div>
            <div className="flex space-x-6">
              <a href="#" className="text-gray-400 hover:text-gray-500">
                Privacy Policy
              </a>
              <a href="#" className="text-gray-400 hover:text-gray-500">
                Terms of Service
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Layout
