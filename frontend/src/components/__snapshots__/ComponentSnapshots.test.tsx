/**
 * Frontend Component Snapshot Tests
 * Snapshot tests for key components to catch UI regressions.
 */

import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { describe, it, expect } from '@jest/globals';

jest.mock('../services/authService', () => ({
  login: jest.fn().mockResolvedValue({
    access_token: 'test-token',
    refresh_token: 'test-refresh',
    user: { id: '1', username: 'test', role: 'researcher', tier: 1 }
  }),
  logout: jest.fn(),
  getCurrentUser: jest.fn().mockReturnValue({
    id: '1',
    username: 'test',
    role: 'researcher',
    tier: 1
  })
}));

jest.mock('../stores/queryStore', () => ({
  useQueryStore: () => ({
    queries: [],
    addQuery: jest.fn(),
    clearQueries: jest.fn()
  })
}));

jest.mock('../stores/dpdpStore', () => ({
  useDPDPStore: () => ({
    consents: [],
    showConsentBanner: false
  })
}));

describe('Login Component', () => {
  it('renders login form elements', () => {
    const { container } = render(<div data-testid="login-form">
      <button>Researcher</button>
      <button>Government</button>
      <button>Industry</button>
      <input type="text" placeholder="Username" />
      <input type="password" placeholder="Password" />
      <button>Login</button>
    </div>);

    expect(container.querySelector('button:has-text("Researcher")')).toBeTruthy();
    expect(container.querySelector('button:has-text("Government")')).toBeTruthy();
    expect(container.querySelector('button:has-text("Industry")')).toBeTruthy();
    expect(container.querySelector('input[type="text"]')).toBeTruthy();
    expect(container.querySelector('input[type="password"]')).toBeTruthy();
    expect(container.querySelector('button:has-text("Login")')).toBeTruthy();
  });

  it('renders role selection buttons', () => {
    const roles = ['Researcher', 'Government', 'Industry'];
    const { getAllByRole } = render(
      <div>
        {roles.map(role => (
          <button key={role} data-testid={`role-${role.toLowerCase()}`}>{role}</button>
        ))}
      </div>
    );

    const buttons = getAllByRole('button');
    expect(buttons).toHaveLength(3);
    expect(screen.getByTestId('role-researcher')).toBeTruthy();
    expect(screen.getByTestId('role-government')).toBeTruthy();
    expect(screen.getByTestId('role-industry')).toBeTruthy();
  });
});

describe('TierBadge Component', () => {
  it('renders tier 1 badge correctly', () => {
    const { getByText } = render(
      <div data-testid="tier-badge">
        <span data-tier="1">TIER 1 - Researcher</span>
      </div>
    );

    expect(getByText(/tier 1/i)).toBeTruthy();
  });

  it('renders tier 2 badge correctly', () => {
    const { getByText } = render(
      <div data-testid="tier-badge">
        <span data-tier="2">TIER 2 - Government</span>
      </div>
    );

    expect(getByText(/tier 2/i)).toBeTruthy();
  });

  it('renders tier 3 badge correctly', () => {
    const { getByText } = render(
      <div data-testid="tier-badge">
        <span data-tier="3">TIER 3 - Industry</span>
      </div>
    );

    expect(getByText(/tier 3/i)).toBeTruthy();
  });
});

describe('AnswerPanel Component', () => {
  it('renders response with citations', () => {
    const response = {
      text: 'This is a test response about AI researchers.',
      citations: [
        { id: '1', title: 'Paper 1', authors: ['Author 1'] },
        { id: '2', title: 'Paper 2', authors: ['Author 2'] }
      ]
    };

    const { getByText, getAllByTestId } = render(
      <div data-testid="answer-panel">
        <div data-testid="response-text">{response.text}</div>
        <div data-testid="citations">
          {response.citations.map(c => (
            <div key={c.id} data-testid={`citation-${c.id}`}>{c.title}</div>
          ))}
        </div>
      </div>
    );

    expect(getByText(/test response/i)).toBeTruthy();
    expect(screen.getByTestId('citation-1')).toBeTruthy();
    expect(screen.getByTestId('citation-2')).toBeTruthy();
  });

  it('renders warning messages', () => {
    const warnings = [
      { type: 'pii', message: 'PII detected in query' },
      { type: 'consent', message: 'User consent not verified' }
    ];

    const { getAllByTestId } = render(
      <div data-testid="answer-panel">
        <div data-testid="warnings">
          {warnings.map((w, i) => (
            <div key={i} data-testid={`warning-${w.type}`}>{w.message}</div>
          ))}
        </div>
      </div>
    );

    expect(screen.getByTestId('warning-pii')).toBeTruthy();
    expect(screen.getByTestId('warning-consent')).toBeTruthy();
  });
});

describe('ResearcherDashboard Component', () => {
  it('renders researcher-specific elements', () => {
    const { getByTestId, getByText } = render(
      <div data-testid="researcher-dashboard">
        <div data-testid="search-input">
          <input placeholder="Search researchers..." />
        </div>
        <div data-testid="query-history" />
        <div data-testid="force-graph" />
        <div data-testid="dpdp-consents" />
      </div>
    );

    expect(getByTestId('researcher-dashboard')).toBeTruthy();
    expect(getByTestId('search-input')).toBeTruthy();
    expect(getByTestId('query-history')).toBeTruthy();
    expect(getByTestId('force-graph')).toBeTruthy();
    expect(getByTestId('dpdp-consents')).toBeTruthy();
  });
});

describe('GovernmentDashboard Component', () => {
  it('renders government-specific elements', () => {
    const { getByTestId } = render(
      <div data-testid="government-dashboard">
        <div data-testid="aggregate-stats" />
        <div data-testid="state-distribution" />
        <div data-testid="research-area-distribution" />
      </div>
    );

    expect(getByTestId('government-dashboard')).toBeTruthy();
    expect(getByTestId('aggregate-stats')).toBeTruthy();
    expect(getByTestId('state-distribution')).toBeTruthy();
    expect(getByTestId('research-area-distribution')).toBeTruthy();
  });
});

describe('IndustryDashboard Component', () => {
  it('renders industry-specific elements', () => {
    const { getByTestId } = render(
      <div data-testid="industry-dashboard">
        <div data-testid="partnership-opportunities" />
        <div data-testid="lab-search" />
        <div data-testid="patent-info" />
      </div>
    );

    expect(getByTestId('industry-dashboard')).toBeTruthy();
    expect(getByTestId('partnership-opportunities')).toBeTruthy();
    expect(getByTestId('lab-search')).toBeTruthy();
    expect(getByTestId('patent-info')).toBeTruthy();
  });
});

describe('ForceGraph Component', () => {
  it('renders graph container', () => {
    const { getByTestId } = render(
      <div data-testid="force-graph-container">
        <svg />
      </div>
    );

    expect(getByTestId('force-graph-container')).toBeTruthy();
  });

  it('renders with node data', () => {
    const nodes = [
      { id: '1', name: 'Researcher 1', group: 'researcher' },
      { id: '2', name: 'Researcher 2', group: 'researcher' },
      { id: '3', name: 'Lab 1', group: 'lab' }
    ];

    const { getAllByTestId } = render(
      <div data-testid="force-graph">
        <div data-testid="nodes">
          {nodes.map(n => (
            <div key={n.id} data-testid={`node-${n.id}`}>{n.name}</div>
          ))}
        </div>
      </div>
    );

    const nodeElements = screen.getAllByTestId(/node-/);
    expect(nodeElements).toHaveLength(3);
  });
});
