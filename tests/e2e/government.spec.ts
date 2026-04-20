import { test, expect } from '@playwright/test';

const API_BASE = 'http://localhost:8000';

test.describe('Government Persona E2E Flow', () => {
  let accessToken: string;

  test.beforeAll(async ({ request }) => {
    const response = await request.post(`${API_BASE}/login`, {
      data: { username: 'gov_user', password: 'gov-pass' },
    });
    if (response.ok()) {
      const data = await response.json();
      accessToken = data.access_token;
    }
  });

  test('login as government user and receive tokens', async ({ request }) => {
    const response = await request.post(`${API_BASE}/login`, {
      data: { username: 'gov_user', password: 'gov-pass' },
    });
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.access_token).toBeDefined();
    expect(data.user.role).toBe('government');
  });

  test('view full stats with distributions as government', async ({ request }) => {
    const response = await request.get(`${API_BASE}/stats`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.total_researchers).toBeDefined();
    expect(data.total_publications).toBeDefined();
    expect(data.total_institutions).toBeDefined();
    expect(data.total_labs).toBeDefined();
    expect(data.research_area_distribution).toBeDefined();
    expect(data.state_distribution).toBeDefined();
  });

  test('view filtered dashboard with state distribution', async ({ request }) => {
    const response = await request.get(`${API_BASE}/stats`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(Array.isArray(data.state_distribution)).toBeTruthy();
  });

  test('query with full tier access', async ({ request }) => {
    const response = await request.post(`${API_BASE}/query`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      data: { query: 'Show all publications by year' },
    });
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.tier).toBeGreaterThanOrEqual(3);
  });
});
