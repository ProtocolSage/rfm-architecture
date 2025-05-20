import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: 'tests',
  fullyParallel: false, // Changed to false since we're testing a desktop app
  reporter: [['html', { open: 'never' }]],
  timeout: 30000, // Longer timeout for desktop app testing
  
  // For desktop app testing, we don't need browser settings
  projects: [
    { name: 'desktop-app' },
  ],
  
  // Additional configuration for snapshot testing
  expect: {
    toMatchSnapshot: { threshold: 0.2 }, // Allow 20% pixel difference to handle platform rendering variations
  },
});