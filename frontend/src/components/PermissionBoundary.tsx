import { useAuth } from '../hooks/useAuth';

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
        <h3 className="text-lg font-semibold text-gray-700">IITGN Access Restricted</h3>
        <p className="text-sm text-gray-500 mt-2">
          Your clearance level ({user?.tier || 'N/A'}) does not permit access to Tier {tier} resources.
        </p>
        <p className="text-xs text-gray-400 mt-1">Contact your institution admin for access escalation.</p>
      </div>
    );
  }
  
  return <>{children}</>;
}
