import { useEffect, useState } from 'react';
export default function DPDPAudit() {
  const [events, setEvents] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/audit/events', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('iitgn_token')}` }
    })
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(data => setEvents(data.events || []))
      .catch(e => setError(e.message));
  }, []);

  return (
    <div className="iitgn-dpdp-audit p-6">
      <h1 className="text-2xl font-bold mb-4">DPDP 2023 Compliance Audit</h1>
      {error && <div className="text-red-600 mb-4">Unable to load audit events. {error}</div>}
      <table className="w-full text-sm border">
        <thead className="bg-gray-100">
          <tr><th className="p-2 border">Time</th><th className="p-2 border">User</th><th className="p-2 border">Action</th></tr>
        </thead>
        <tbody>
          {events.map((ev, idx) => (
            <tr key={idx} className="border-b">
              <td className="p-2 border">{ev.timestamp}</td>
              <td className="p-2 border">{ev.user_id}</td>
              <td className="p-2 border">{ev.action}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
