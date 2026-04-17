import React, { useState } from 'react'
import { LoaderIcon, SearchIcon } from './Icons'
import { useAuth } from '../hooks/useAuth'

interface SearchBarProps {
  onSearch: (query: string) => void
  isLoading?: boolean
  placeholder?: string
}

const SearchBar: React.FC<SearchBarProps> = ({ 
  onSearch, 
  isLoading = false, 
  placeholder = "Ask anything about research in India..." 
}) => {
  const [query, setQuery] = useState('')
  const { user } = useAuth()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim() && !isLoading) {
      onSearch(query.trim())
    }
  }

  const getPersonaPlaceholder = () => {
    if (!user) return placeholder
    
    switch (user.tier) {
      case 1:
        return "Find researchers, publications, or collaborations..."
      case 2:
        return "Analyze funding trends, institutional performance..."
      case 3:
        return "Discover technical capabilities, partnership opportunities..."
      default:
        return placeholder
    }
  }

  return (
    <form onSubmit={handleSubmit} className="relative w-full max-w-2xl">
      <div className="relative">
        <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={getPersonaPlaceholder()}
          className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={isLoading}
        />
        {isLoading && (
          <LoaderIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 animate-spin text-blue-500 w-5 h-5" />
        )}
      </div>
      <button
        type="submit"
        className="sr-only"
        disabled={isLoading || !query.trim()}
      >
        Search
      </button>
    </form>
  )
}

export default SearchBar
