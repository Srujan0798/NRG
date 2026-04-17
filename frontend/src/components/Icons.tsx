import React from 'react'

type IconProps = React.SVGProps<SVGSVGElement>

const BaseIcon: React.FC<IconProps & { children: React.ReactNode }> = ({ children, ...props }) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.8"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
    {...props}
  >
    {children}
  </svg>
)

export const SearchIcon: React.FC<IconProps> = (props) => (
  <BaseIcon {...props}>
    <circle cx="11" cy="11" r="7" />
    <path d="m20 20-3.5-3.5" />
  </BaseIcon>
)

export const LoaderIcon: React.FC<IconProps> = (props) => (
  <BaseIcon {...props}>
    <path d="M21 12a9 9 0 1 1-9-9" />
  </BaseIcon>
)

export const UserIcon: React.FC<IconProps> = (props) => (
  <BaseIcon {...props}>
    <path d="M20 21a8 8 0 0 0-16 0" />
    <circle cx="12" cy="8" r="4" />
  </BaseIcon>
)

export const Building2Icon: React.FC<IconProps> = (props) => (
  <BaseIcon {...props}>
    <path d="M6 22V6l6-3 6 3v16" />
    <path d="M3 22h18" />
    <path d="M10 10h4" />
    <path d="M10 14h4" />
    <path d="M10 18h4" />
  </BaseIcon>
)

export const BuildingIcon: React.FC<IconProps> = (props) => (
  <BaseIcon {...props}>
    <path d="M4 22V7l8-4 8 4v15" />
    <path d="M9 10h.01" />
    <path d="M15 10h.01" />
    <path d="M9 14h.01" />
    <path d="M15 14h.01" />
    <path d="M10 22v-4h4v4" />
  </BaseIcon>
)

export const LogInIcon: React.FC<IconProps> = (props) => (
  <BaseIcon {...props}>
    <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
    <path d="M10 17l5-5-5-5" />
    <path d="M15 12H3" />
  </BaseIcon>
)

export const LogOutIcon: React.FC<IconProps> = (props) => (
  <BaseIcon {...props}>
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
    <path d="M16 17l5-5-5-5" />
    <path d="M21 12H9" />
  </BaseIcon>
)

export const ShieldCheckIcon: React.FC<IconProps> = (props) => (
  <BaseIcon {...props}>
    <path d="M12 3l7 4v5c0 5-3.5 8-7 9-3.5-1-7-4-7-9V7l7-4Z" />
    <path d="m9 12 2 2 4-4" />
  </BaseIcon>
)

export const BarChart3Icon: React.FC<IconProps> = (props) => (
  <BaseIcon {...props}>
    <path d="M3 3v18h18" />
    <path d="M7 14v4" />
    <path d="M12 10v8" />
    <path d="M17 6v12" />
  </BaseIcon>
)

export const AtomIcon: React.FC<IconProps> = (props) => (
  <BaseIcon {...props}>
    <circle cx="12" cy="12" r="1.5" />
    <path d="M6 12c0-4 2.5-7 6-7s6 3 6 7-2.5 7-6 7-6-3-6-7Z" />
    <path d="M8 6c3 2 5 5 5 6s-2 4-5 6" />
    <path d="M16 6c-3 2-5 5-5 6s2 4 5 6" />
  </BaseIcon>
)

export const SparklesIcon: React.FC<IconProps> = (props) => (
  <BaseIcon {...props}>
    <path d="m12 3 1.8 4.2L18 9l-4.2 1.8L12 15l-1.8-4.2L6 9l4.2-1.8L12 3Z" />
    <path d="m19 14 1 2.5L22.5 17 20 18l-1 2.5L18 18l-2.5-1 2.5-.5L19 14Z" />
    <path d="m5 14 .8 2 2 .8-2 .8L5 20l-.8-2.4L2 16.8l2.2-.8L5 14Z" />
  </BaseIcon>
)

export const FileTextIcon: React.FC<IconProps> = (props) => (
  <BaseIcon {...props}>
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <path d="M14 2v6h6" />
    <path d="M8 13h8" />
    <path d="M8 17h6" />
  </BaseIcon>
)

export const ExternalLinkIcon: React.FC<IconProps> = (props) => (
  <BaseIcon {...props}>
    <path d="M14 3h7v7" />
    <path d="M10 14 21 3" />
    <path d="M21 14v4a3 3 0 0 1-3 3H6a3 3 0 0 1-3-3V6a3 3 0 0 1 3-3h4" />
  </BaseIcon>
)
