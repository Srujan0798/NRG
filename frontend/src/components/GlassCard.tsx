import React from 'react';

export interface GlassCardProps {
  children: React.ReactNode;
  accent?: 'researcher' | 'government' | 'industry' | 'sovereign';
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  onClick?: () => void;
  className?: string;
  hover?: boolean;
}

const ACCENT_MAP: Record<string, string> = {
  researcher: 'border-l-researcher-500',
  government: 'border-l-government-500',
  industry: 'border-l-industry-500',
  sovereign: 'border-l-sovereign-500',
};

const ICON_BG_MAP: Record<string, string> = {
  researcher: 'bg-researcher-100 text-researcher-700',
  government: 'bg-government-100 text-government-700',
  industry: 'bg-industry-100 text-industry-700',
  sovereign: 'bg-sovereign-100 text-sovereign-700',
};

export function GlassCard({
  children,
  accent = 'researcher',
  title,
  description,
  icon,
  onClick,
  className = '',
  hover = true,
}: GlassCardProps) {
  return (
    <div
      className={`
        iitgn-glass-card border-l-4 ${ACCENT_MAP[accent]} 
        ${hover ? 'cursor-pointer hover:shadow-xl hover:-translate-y-1' : ''}
        ${className}
      `}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => e.key === 'Enter' && onClick() : undefined}
    >
      {(title || icon) && (
        <div className="flex items-center gap-3 mb-3">
          {icon && (
            <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${ICON_BG_MAP[accent]}`}>
              {icon}
            </div>
          )}
          <div>
            {title && <h3 className="text-lg font-semibold text-gray-800">{title}</h3>}
            {description && <p className="text-sm text-gray-500">{description}</p>}
          </div>
        </div>
      )}
      {children}
    </div>
  );
}
