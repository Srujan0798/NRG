import React from 'react'
import { BookOpen, BarChart3, Building2, SlidersHorizontal, Users } from 'lucide-react'
import { t } from '../../i18n'
import {
  productionWorkspaceRoutes,
  type ProductionWorkspaceScreen,
  type ProductionWorkspaceRoute,
} from '../productionWorkspaceConfig'

const routeIcons: Record<ProductionWorkspaceScreen, React.ElementType> = {
  publications: BookOpen,
  researchers: Users,
  reports: BarChart3,
  industry: Building2,
  settings: SlidersHorizontal,
}

function getRoute(screen: ProductionWorkspaceScreen): ProductionWorkspaceRoute {
  return productionWorkspaceRoutes.find((route) => route.screen === screen) || productionWorkspaceRoutes[0]
}

interface ScreenHeaderProps {
  screen: ProductionWorkspaceScreen
  user: { tier: number; role: string }
}

export const ScreenHeader: React.FC<ScreenHeaderProps> = ({ screen, user }) => {
  const activeRoute = getRoute(screen)
  const Icon = routeIcons[screen]

  return (
    <section className="rounded-3xl border border-nrg-border bg-[var(--nrg-surface)] p-6 shadow-sm">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex gap-4">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-[var(--glass-bg)] text-nrg-text">
            <Icon size={24} aria-hidden="true" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-nrg-muted">
              {t('productionWorkspace.common.workspace')}
            </p>
            <h1 className="mt-2 text-3xl font-bold text-nrg-text">{t(activeRoute.labelKey)}</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-nrg-muted">
              {t(activeRoute.descriptionKey)}
            </p>
          </div>
        </div>
        <div className="rounded-2xl border border-nrg-border bg-[var(--glass-bg)] px-4 py-3">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-nrg-muted">
            {t('productionWorkspace.common.activeAccess')}
          </p>
          <p className="mt-1 text-sm font-semibold text-nrg-text">
            {t('productionWorkspace.common.tierLabel', { tier: user.tier, role: user.role })}
          </p>
        </div>
      </div>
    </section>
  )
}
