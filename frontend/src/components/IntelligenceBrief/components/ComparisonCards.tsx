import React, { useMemo } from 'react'

interface ComparisonCardsProps {
  response: string
}

export const ComparisonCards: React.FC<ComparisonCardsProps> = ({ response }) => {
  const comparisons = useMemo(() => {
    const sections = response.split(/(?:compare|vs|versus|whereas|however)/gi)
    if (sections.length < 2) {
      const lines = response.split('\n').filter(l => l.trim())
      const mid = Math.ceil(lines.length / 2)
      return [
        { title: 'Option A', content: lines.slice(0, mid).join('\n') },
        { title: 'Option B', content: lines.slice(mid).join('\n') },
      ]
    }
    return sections.slice(1).map((s, i) => ({
      title: s.split('\n')[0]?.substring(0, 50) || `Option ${i + 1}`,
      content: s,
    }))
  }, [response])

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {comparisons.map((item, i) => (
        <div 
          key={i}
          className={`p-4 rounded-xl border ${
            i === 0 
              ? 'bg-blue-50 border-blue-200' 
              : 'bg-purple-50 border-purple-200'
          }`}
        >
          <h4 className={`text-sm font-semibold mb-2 ${
            i === 0 ? 'text-blue-700' : 'text-purple-700'
          }`}>
            {item.title}
          </h4>
          <p className="text-sm text-nrg-text leading-relaxed">
            {item.content}
          </p>
        </div>
      ))}
    </div>
  )
}

export default ComparisonCards