#!/bin/bash
# Execute in: /Users/roshwinram/Desktop/National-Research-Graph/frontend/src/
# Target: IITGN Multi-Tier UI

echo "[BETA-2] Persona-Specific UI Workspaces"
# 1. Add RBAC-aware components
cat > components/PermissionBoundary.tsx << 'EOF'
import { useAuth } from '../hooks/useAuth';
export function PermissionBoundary({ tier, children }) {
  const { user } = useAuth();
  
  if (user?.tier > tier) {
    return <div className="iitgn-access-denied">🔒 IITGN ss Restricted</div>;
  }
  
  return <>{children}</>;
}
EOF

# 2. Build persona dashboards
npx vite build --config vite.researcher.config.ts
npx vite build --config vite.government.config.ts  
npx vite build --config vite.industry.config.ts

# 3. Deploy to different paths
mv dist/researcher /var/www/iitgn/researcher
mv dist/government /var/www/iitgn/government
mv dist/industry /var/www/iitgn/industry

echo "[BETA-2] Persona Workspaces Deployed"