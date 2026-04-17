# Playwright Testing for National Research Graph

This directory contains automated tests for the National Research Graph frontend using Playwright.

## Test Coverage

The tests cover the following functionality:

1. **Login Functionality**
   - Login for all user roles (researcher, government, industry)
   - Error handling for invalid credentials

2. **Role-based Access Controls**
   - Verification that each role sees appropriate dashboard elements
   - Navigation between dashboard tabs

3. **DPDP Consent Functionality**
   - Granting and withdrawing DPDP consent
   - Consent dialog interactions

4. **Audit Log Functionality**
   - Display of audit entries
   - Clear log functionality

5. **Graph Visualization**
   - Graph loading and interactivity
   - Node click interactions

6. **Responsive Design**
   - Application behavior on different screen sizes

## Running Tests

To run the tests, use the following commands:

```bash
# Run all tests
npx playwright test

# Run tests in headed mode (to see the browser)
npx playwright test --headed

# Run tests with trace enabled (for debugging)
npx playwright test --trace on

# Run tests for a specific file
npx playwright test tests/login.spec.ts
```

## Test Structure

- `login.spec.ts` - Tests login functionality for all user roles
- `role-access.spec.ts` - Tests role-based access controls
- `consent.spec.ts` - Tests DPDP consent functionality
- `audit-log.spec.ts` - Tests audit log functionality
- `graph-visualization.spec.ts` - Tests graph visualization functionality
- `responsive.spec.ts` - Tests responsive design across different screen sizes

## Prerequisites

1. The frontend application must be running on `http://localhost:3000`
2. Playwright must be installed: `npm install -D @playwright/test`
3. Install browser dependencies: `npx playwright install`