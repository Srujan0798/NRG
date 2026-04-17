# Playwright Tests for National Research Graph Frontend

This document summarizes the Playwright tests created for the National Research Graph frontend to verify functionality across different user roles and features.

## Test Files Created

1. **basic.spec.ts** - Basic page loading test
2. **login.spec.ts** - Login functionality tests for all user roles
3. **role-access.spec.ts** - Tests for user role access and restrictions
4. **consent.spec.ts** - Tests for DPDP consent functionality
5. **audit-log.spec.ts** - Tests for audit log functionality
6. **graph-visualization.spec.ts** - Tests for graph visualization features
7. **responsive.spec.ts** - Tests for responsive design across different screen sizes

## Test Coverage

### 1. Login Functionality Tests
- Test login for researcher, government, and industry roles
- Test invalid login scenarios
- Test navigation after successful login

### 2. Role Access Tests
- Verify each user role can access their appropriate dashboard
- Ensure role-based access control is working correctly
- Test cross-role access restrictions

### 3. Navigation Tests
- Test navigation between different dashboard tabs
- Verify that all UI elements are accessible

### 4. DPDP Consent Functionality Tests
- Test viewing and managing DPDP consent
- Test consent dialog functionality
- Test consent acceptance and withdrawal

### 5. Audit Log Functionality Tests
- Test viewing audit log entries
- Test filtering and exporting audit logs

### 6. Graph Visualization Tests
- Test graph rendering and interaction
- Test node interaction
- Test responsive design across different viewports

### 7. Responsive Design Tests
- Test desktop, tablet, and mobile layouts
- Test navigation adaptation to different screen sizes
- Test form elements responsiveness

## Running the Tests

To run the tests:

```bash
# Run all tests
npm run test:e2e

# Run specific test file
npm run test:e2e basic.spec.ts
npm run test:e2e login.spec.ts
npm run test:e2e role-access.spec.ts
npm run test:e2e consent.spec.ts
npm run test:e2e audit-log.spec.ts
npm run test:e2e graph-visualization.spec.ts
npm run test:e2e responsive.spec.ts
```

## Test Configuration

The tests are configured to run against the local development server and use the test personas defined in the application:
- Researcher: username 'researcher_user', password 'researcher-pass'
- Government: username 'gov_user', password 'government-pass'
- Industry: username 'industry_user', password 'industry-pass'