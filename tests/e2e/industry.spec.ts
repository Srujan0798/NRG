import { test, expect } from '@playwright/test';

const API_BASE = 'http://localhost:8000';

test.describe('Industry Persona E2E Flow', () => {
  let accessToken: string;

  test.beforeAll(async ({ request }) => {
    const response = await request.post(`${API_BASE}/login`, {
      data: { username: 'industry', password: 'industry-pass' },
    });
    if (response.ok()) {
      const data = await response.json();
      accessToken = data.access_token;
    }
  });

  test('login as industry user and receive tokens', async ({ request }) => {
    const response = await request.post(`${API_BASE}/login`, {
      data: { username: 'industry', password: 'industry-pass' },
    });
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.access_token).toBeDefined();
    expect(data.user.role).toBe('industry');
  });

  test('view limited stats as industry', async ({ request }) => {
    const response = await request.get(`${API_BASE}/stats`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.total_researchers).toBeDefined();
    expect(data.total_publications).toBeDefined();
    expect(data.total_institutions).toBeUndefined();
    expect(data.total_labs).toBeUndefined();
    expect(data.research_areas).toBeDefined();
  });

  test('tier restrictions enforced on query', async ({ request }) => {
    const response = await request.post(`${API_BASE}/query`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      data: { query: 'Show me publications in AI' },
    });
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.tier).toBeLessThanOrEqual(2);
  });

  test('graph data returns limited view', async ({ request }) => {
    const response = await request.get(`${API_BASE}/query/graph`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      params: { topic: 'AI' },
    });
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.nodes).toBeDefined();
    expect(data.edges).toBeDefined();
  });
});
