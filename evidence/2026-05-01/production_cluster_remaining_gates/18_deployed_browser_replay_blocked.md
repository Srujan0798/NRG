# Deployed Browser Replay Gate

Status: BLOCKED

Reason: no deployed application URL is configured in this shell.

Evidence:

- `PLAYWRIGHT_BASE_URL=UNSET`
- `NRG_PRODUCTION_URL=UNSET`
- `API_TARGET=UNSET`
- `NRG_API_URL=UNSET`

Required next command after a deployed URL exists:

```bash
PLAYWRIGHT_BASE_URL="https://<deployed-nrg-host>" \
  npm --prefix frontend run test:e2e
```

Acceptance before this can pass:

- Browser runs against the deployed host, not local Vite.
- Login -> persona/tier -> messy query -> streaming answer -> citations/source drawer -> audit drawer completes.
- Desktop and mobile screenshots are saved under evidence.
- Console/network logs contain no unexplained errors.
