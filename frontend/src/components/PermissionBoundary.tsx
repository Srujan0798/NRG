import { useAuth } from '../hooks/useAuth';
import { t } from '../i18n'

export interface PermissionBoundaryProps {
  tier: number;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function PermissionBoundary({ tier, children, fallback }: PermissionBoundaryProps) {
  const { user } = useAuth();
  
  if (user?.tier > tier) {
    return fallback ? <>{fallback}</> : (
      <div className="iitgn-access-denied flex flex-col items-center justify-center p-8 bg-gray-50 rounded-lg border border-gray-200">
        <span className="text-4xl mb-4">🔒</span>
        <h3 className="text-lg font-semibold text-gray-700">{t("auto.components.PermissionBoundary.1")}</h3>
        <p className="text-sm text-gray-500 mt-2">
          {t("auto.components.PermissionBoundary.2")}{user?.tier || 'unavailable'}{t("auto.components.PermissionBoundary.3")}{tier} {t("auto.components.PermissionBoundary.4")}</p>
        <p className="text-xs text-gray-400 mt-1">{t("auto.components.PermissionBoundary.5")}</p>
      </div>
    );
  }
  
  return <>{children}</>;
}
