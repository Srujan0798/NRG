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
