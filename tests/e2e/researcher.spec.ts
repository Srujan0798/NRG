import { test, expect } from '@playwright/test';

const API_BASE = 'http://localhost:8000';

test.describe('Researcher Persona E2E Flow', () => {
  let accessToken: string;

  test.beforeAll(async ({ request }) => {
    const response = await request.post(`${API_BASE}/login`, {
      data: { username: 'researcher', password: 'researcher-pass' },
    });
    if (response.ok()) {
      const data = await response.json();
      accessToken = data.access_token;
    }
  });

  test('login as researcher and receive tokens', async ({ request }) => {
    const response = await request.post(`${API_BASE}/login`, {
      data: { username: 'researcher', password: 'researcher-pass' },
    });
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.access_token).toBeDefined();
    expect(data.user.role).toBe('researcher');
  });

  test('submit query and receive response with citations', async ({ request }) => {
    const response = await request.post(`${API_BASE}/query`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      data: { query: 'Show me researchers in AI' },
    });
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.status).toBe('success');
    expect(data.query_id).toBeDefined();
    expect(data.citations).toBeDefined();
  });

  test('view stats as researcher', async ({ request }) => {
    const response = await request.get(`${API_BASE}/stats`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.total_researchers).toBeDefined();
    expect(data.total_publications).toBeDefined();
    expect(data.total_institutions).toBeDefined();
  });

  test('export data via DPDP endpoint', async ({ request }) => {
    const response = await request.get(`${API_BASE}/me/data`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.user_id).toBeDefined();
  });
});
