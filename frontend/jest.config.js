/** @type {import('ts-jest').JestConfigWithTsJest} */
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  roots: [
    '<rootDir>/src',
    '<rootDir>/tests/components',
    '<rootDir>/tests/design-system',
    '<rootDir>/tests/hooks',
    '<rootDir>/tests/i18n',
    '<rootDir>/tests/a11y',
  ],
  testPathIgnorePatterns: [
    '/node_modules/',
    '/e2e/',
    '/dist/',
  ],
  moduleNameMapper: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },
};
