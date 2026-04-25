import { useState, useEffect } from 'react';

interface RateLimitStatus {
  requestsPerMinute: number;
  limit: number;
  remaining: number;
  resetAt: number;
  blocked: boolean;
}

export function SecurityMonitor() {
  const [rateLimit, setRateLimit] = useState<RateLimitStatus>({
    requestsPerMinute: 0,
    limit: 60,
    remaining: 60,
    resetAt: Date.now() + 60000,
    blocked: false,
  });

  const [requestHistory, setRequestHistory] = useState<number[]>([]);

  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      const recent = requestHistory.filter((ts) => now - ts < 60000);
      const remaining = Math.max(0, rateLimit.limit - recent.length);
      
      setRateLimit({
        requestsPerMinute: recent.length,
        limit: rateLimit.limit,
        remaining,
        resetAt: now + 60000,
        blocked: remaining === 0,
      });
      setRequestHistory(recent);
    }, 1000);

    return () => clearInterval(interval);
  }, [requestHistory, rateLimit.limit]);

  const trackRequest = () => {
    setRequestHistory((prev) => [...prev, Date.now()]);
  };

  const percentage = (rateLimit.remaining / rateLimit.limit) * 100;
  const barColor = percentage > 50 ? 'bg-green-500' : percentage > 20 ? 'bg-amber-500' : 'bg-red-500';

  return (
    <div className="nrg-panel overflow-hidden">
      <div className="px-4 py-3 border-b border-nrg-border bg-[var(--glass-bg)]">
        <h3 className="font-semibold text-nrg-text">Security Guardrails</h3>
        <p className="text-xs text-nrg-muted">Rate limiting, masked IP audit, and abuse protection</p>
      </div>

      <div className="p-4 space-y-4">
        {/* Rate Limit */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-nrg-text">Rate Limit</span>
            <span className={`text-xs font-mono px-2 py-0.5 rounded ${
              rateLimit.blocked
                ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                : 'bg-[var(--glass-bg)] text-nrg-muted'
            }`}>
              {rateLimit.remaining}/{rateLimit.limit} req/min
            </span>
          </div>
          <div className="w-full bg-[var(--nrg-border)] rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${barColor}`}
              style={{ width: `${percentage}%` }}
            />
          </div>
          <div className="flex items-center justify-between mt-1 text-xs text-nrg-muted">
            <span>{rateLimit.requestsPerMinute} requests this minute</span>
            <span>Resets in {Math.ceil((rateLimit.resetAt - Date.now()) / 1000)}s</span>
          </div>
        </div>

        {/* Simulated IP */}
        <div className="rounded-lg border border-nrg-border bg-[var(--glass-bg)] p-3 text-xs">
          <div className="text-nrg-muted mb-1">Tracked Session IP</div>
          <div className="font-mono text-nrg-text">192.168.1.xxx (masked)</div>
          <div className="text-nrg-muted mt-1">All requests are retained in the sovereign audit trail.</div>
        </div>

        <button
          onClick={trackRequest}
          className="min-h-11 w-full rounded-lg border border-nrg-border bg-[var(--glass-bg)] px-3 py-2 text-sm font-medium text-nrg-text transition hover:bg-saffron-500/10"
        >
          Run Local Safety Check
        </button>

        {rateLimit.blocked && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-xs text-red-700">
            Rate limit exceeded. Please wait before making more requests.
          </div>
        )}
      </div>
    </div>
  );
}
