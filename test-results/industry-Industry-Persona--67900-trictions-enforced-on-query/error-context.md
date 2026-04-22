# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: industry.spec.ts >> Industry Persona E2E Flow >> tier restrictions enforced on query
- Location: tests/e2e/industry.spec.ts:41:7

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
  5  | test.describe('Industry Persona E2E Flow', () => {
  6  |   let accessToken: string;
  7  | 
  8  |   test.beforeAll(async ({ request }) => {
  9  |     const response = await request.post(`${API_BASE}/login`, {
  10 |       data: { username: 'industry_user', password: 'industry-pass' },
  11 |     });
  12 |     if (response.ok()) {
  13 |       const data = await response.json();
  14 |       accessToken = data.access_token;
  15 |     }
  16 |   });
  17 | 
  18 |   test('login as industry user and receive tokens', async ({ request }) => {
  19 |     const response = await request.post(`${API_BASE}/login`, {
  20 |       data: { username: 'industry_user', password: 'industry-pass' },
  21 |     });
  22 |     expect(response.ok()).toBeTruthy();
  23 |     const data = await response.json();
  24 |     expect(data.access_token).toBeDefined();
  25 |     expect(data.user.role).toBe('industry');
  26 |   });
  27 | 
  28 |   test('view limited stats as industry', async ({ request }) => {
  29 |     const response = await request.get(`${API_BASE}/stats`, {
  30 |       headers: { Authorization: `Bearer ${accessToken}` },
  31 |     });
  32 |     expect(response.ok()).toBeTruthy();
  33 |     const data = await response.json();
  34 |     expect(data.total_researchers).toBeDefined();
  35 |     expect(data.total_publications).toBeDefined();
  36 |     expect(data.total_institutions).toBeUndefined();
  37 |     expect(data.total_labs).toBeUndefined();
  38 |     expect(data.research_areas).toBeDefined();
  39 |   });
  40 | 
  41 |   test('tier restrictions enforced on query', async ({ request }) => {
  42 |     const response = await request.post(`${API_BASE}/query`, {
  43 |       headers: { Authorization: `Bearer ${accessToken}` },
  44 |       data: { query: 'Show me publications in AI' },
  45 |     });
> 46 |     expect(response.ok()).toBeTruthy();
     |                           ^ Error: expect(received).toBeTruthy()
  47 |     const data = await response.json();
  48 |     expect(data.tier).toBeLessThanOrEqual(2);
  49 |   });
  50 | 
  51 |   test('graph data returns limited view', async ({ request }) => {
  52 |     const response = await request.get(`${API_BASE}/query/graph`, {
  53 |       headers: { Authorization: `Bearer ${accessToken}` },
  54 |       params: { topic: 'AI' },
  55 |     });
  56 |     expect(response.ok()).toBeTruthy();
  57 |     const data = await response.json();
  58 |     expect(data.nodes).toBeDefined();
  59 |     expect(data.edges).toBeDefined();
  60 |   });
  61 | });
  62 | 
```