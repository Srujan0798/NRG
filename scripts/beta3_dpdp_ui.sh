#!/bin/bash
# Execute in: /Users/roshwinram/Desktop/National-Research-Graph/
# Target: IITGN DPDP 2023 Transparency Requirements

echo "[BETA-3] DPDP Compliance Dashboard"
# 1. Generate DPDP audit log viewer
python3 scripts/compliance/run_dpdp_assessment.py --format=ui

# 2. Add audit log to researcher UI
cat > frontend/src/pages/DPDP-Audit.tsx << 'EOF'
import { useEffect, useState } from 'react';
import { IITGN_LOGO } from '../assets';
export default function DPDPAudit() {
  const [logs, setLogs] = useState([]);
  
  useEffect(() => {
    fetch('/api/audit/logs', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('iitgn_token')}` }
    }).then(r => r.json()).then(setLogs);
  }, []);
  
  return (
    <div className="iitgn-dpdp-audit">
      <h1>IITGN DPDP 2023 Compliance</h1>
      <table>
        <thead>
          <tr><th>Timestamp</th><th>PII Type</th><th>Blocked</th></tr>
        </thead>
        <tbody>
          {logs.map(log => (
            <tr key={log.id}>
              <td>{log.timestamp}</td>
              <td>{log.pii_type}</td>
              <td>{log.blocked ? '✅' : '❌'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
EOF

# 3. Build compliance report for IITGN legal
python3 scripts/compliance/compile_final_docs.py \
  --output docs/IITGN_DPDP_CERTIFICATE_2025.pdf

echo "[BETA-3] DPDP Dashboard Active"