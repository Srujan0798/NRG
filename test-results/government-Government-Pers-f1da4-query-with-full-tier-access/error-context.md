# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: government.spec.ts >> Government Persona E2E Flow >> query with full tier access
- Location: tests/e2e/government.spec.ts:51:7

# Error details

```
Error: expect(received).toBeTruthy()

Received: false
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | const API_BASE = 'http://localhost:8000';
  4  | 
  5  | test.describe('Government Persona E2E Flow', () => {
  6  |   let accessToken: string;
  7  | 
  8  |   test.beforeAll(async ({ request }) => {
  9  |     const response = await request.post(`${API_BASE}/login`, {
  10 |       data: { username: 'gov_user', password: 'gov-pass' },
  11 |     });
  12 |     if (response.ok()) {
  13 |       const data = await response.json();
  14 |       accessToken = data.access_token;
  15 |     }
  16 |   });
  17 | 
  18 |   test('login as government user and receive tokens', async ({ request }) => {
  19 |     const response = await request.post(`${API_BASE}/login`, {
  20 |       data: { username: 'gov_user', password: 'gov-pass' },
  21 |     });
  22 |     expect(response.ok()).toBeTruthy();
  23 |     const data = await response.json();
  24 |     expect(data.access_token).toBeDefined();
  25 |     expect(data.user.role).toBe('government');
  26 |   });
  27 | 
  28 |   test('view full stats with distributions as government', async ({ request }) => {
  29 |     const response = await request.get(`${API_BASE}/stats`, {
  30 |       headers: { Authorization: `Bearer ${accessToken}` },
  31 |     });
  32 |     expect(response.ok()).toBeTruthy();
  33 |     const data = await response.json();
  34 |     expect(data.total_researchers).toBeDefined();
  35 |     expect(data.total_publications).toBeDefined();
  36 |     expect(data.total_institutions).toBeDefined();
  37 |     expect(data.total_labs).toBeDefined();
  38 |     expect(data.research_area_distribution).toBeDefined();
  39 |     expect(data.state_distribution).toBeDefined();
  40 |   });
  41 | 
  42 |   test('view filtered dashboard with state distribution', async ({ request }) => {
  43 |     const response = await request.get(`${API_BASE}/stats`, {
  44 |       headers: { Authorization: `Bearer ${accessToken}` },
  45 |     });
  46 |     expect(response.ok()).toBeTruthy();
  47 |     const data = await response.json();
  48 |     expect(Array.isArray(data.state_distribution)).toBeTruthy();
  49 |   });
  50 | 
  51 |   test('query with full tier access', async ({ request }) => {
  52 |     const response = await request.post(`${API_BASE}/query`, {
  53 |       headers: { Authorization: `Bearer ${accessToken}` },
  54 |       data: { query: 'Show all publications by year' },
  55 |     });
> 56 |     expect(response.ok()).toBeTruthy();
     |                           ^ Error: expect(received).toBeTruthy()
  57 |     const data = await response.json();
  58 |     expect(data.tier).toBeGreaterThanOrEqual(3);
  59 |   });
  60 | });
  61 | 
```