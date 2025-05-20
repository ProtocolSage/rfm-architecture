import { test, expect } from '@playwright/test';

/**
 * WebSocket Connection Resilience E2E Tests
 * 
 * These tests verify that the UI properly handles WebSocket connections,
 * reconnections, and displays appropriate status indicators to users.
 */

test.describe('WebSocket Connection Resilience', () => {
  test('displays connection status within timeout period', async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
    
    // Verify connection status badge updates to "Connected"
    const statusBadge = page.locator('[data-testid="connection-status"]');
    await expect(statusBadge).toBeVisible({ timeout: 5000 });
    await expect(statusBadge).toHaveText('Connected', { timeout: 5000 });
  });

  test('shows reconnecting state during connection issues', async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
    
    // Wait for initial connection
    const statusBadge = page.locator('[data-testid="connection-status"]');
    await expect(statusBadge).toHaveText('Connected', { timeout: 5000 });
    
    // Force disconnect WebSocket
    await page.evaluate(() => {
      // Find and close all active WebSockets
      const wsInstances = Array.from(
        document.querySelectorAll('[data-ws-instance]')
      ).map(el => (el as any).__ws_instance);
      
      wsInstances.forEach((ws: WebSocket) => {
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.close(3000, 'Test-initiated disconnection');
        }
      });
      
      // If no instances found through data attributes, dispatch custom event
      if (wsInstances.length === 0) {
        window.dispatchEvent(new CustomEvent('test:disconnect-websocket'));
      }
    });
    
    // Verify reconnecting state is shown
    await expect(statusBadge).toHaveText('Reconnecting...', { timeout: 2000 });
    
    // Wait for automatic reconnection
    await expect(statusBadge).toHaveText('Connected', { timeout: 10000 });
  });

  test('handles complete render flow with progress updates', async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
    
    // Wait for connection
    const statusBadge = page.locator('[data-testid="connection-status"]');
    await expect(statusBadge).toHaveText('Connected', { timeout: 5000 });
    
    // Start a render
    await page.click('[data-testid="render-button"]');
    
    // Verify progress bar appears
    const progressBar = page.locator('[data-testid="progress-bar"]');
    await expect(progressBar).toBeVisible({ timeout: 2000 });
    
    // Verify progress indicator updates
    const progressPercent = page.locator('[data-testid="progress-percent"]');
    await expect(progressPercent).toBeVisible();
    
    // Verify ETA indicator appears
    const etaDisplay = page.locator('[data-testid="eta-display"]');
    await expect(etaDisplay).toBeVisible();
    
    // Wait for completion (adjust timeout as needed for your render times)
    await expect(progressBar).toHaveAttribute('aria-valuenow', '100', { 
      timeout: 30000 
    });
    
    // Verify render result appears
    await expect(page.locator('[data-testid="render-result"]')).toBeVisible({ 
      timeout: 2000 
    });
  });

  test('successfully cancels operations', async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
    
    // Wait for connection
    const statusBadge = page.locator('[data-testid="connection-status"]');
    await expect(statusBadge).toHaveText('Connected', { timeout: 5000 });
    
    // Start a render
    await page.click('[data-testid="render-button"]');
    
    // Verify progress started
    const progressBar = page.locator('[data-testid="progress-bar"]');
    await expect(progressBar).toBeVisible({ timeout: 2000 });
    
    // Cancel the operation
    await page.click('[data-testid="cancel-button"]');
    
    // Verify cancellation resets UI
    await expect(page.locator('[data-testid="render-button"]')).toBeEnabled({ 
      timeout: 2000 
    });
    
    // Verify progress bar is reset or hidden
    await expect(progressBar).toHaveAttribute('aria-valuenow', '0', { 
      timeout: 2000 
    });
  });

  test('preserves operation state during reconnection', async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
    
    // Wait for connection
    const statusBadge = page.locator('[data-testid="connection-status"]');
    await expect(statusBadge).toHaveText('Connected', { timeout: 5000 });
    
    // Start a render with higher complexity to ensure it runs long enough
    await page.locator('[data-testid="complexity-slider"]').fill('8');
    await page.click('[data-testid="render-button"]');
    
    // Verify progress started
    const progressBar = page.locator('[data-testid="progress-bar"]');
    await expect(progressBar).toBeVisible({ timeout: 2000 });
    
    // Wait for progress to reach at least 20%
    const progressPercent = page.locator('[data-testid="progress-percent"]');
    await expect(async () => {
      const text = await progressPercent.textContent() || '0%';
      const value = parseInt(text.replace('%', ''));
      expect(value).toBeGreaterThanOrEqual(20);
    }).toPass({ timeout: 10000 });
    
    // Force disconnect WebSocket
    await page.evaluate(() => {
      window.dispatchEvent(new CustomEvent('test:disconnect-websocket'));
    });
    
    // Verify reconnecting state
    await expect(statusBadge).toHaveText('Reconnecting...', { timeout: 2000 });
    
    // Wait for reconnection
    await expect(statusBadge).toHaveText('Connected', { timeout: 10000 });
    
    // Verify operation continues from previous progress
    await expect(async () => {
      const text = await progressPercent.textContent() || '0%';
      const value = parseInt(text.replace('%', ''));
      expect(value).toBeGreaterThan(20);
    }).toPass({ timeout: 5000 });
    
    // Verify operation completes successfully
    await expect(progressBar).toHaveAttribute('aria-valuenow', '100', { 
      timeout: 60000 
    });
  });

  test('displays appropriate error messages', async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
    
    // Wait for connection
    const statusBadge = page.locator('[data-testid="connection-status"]');
    await expect(statusBadge).toHaveText('Connected', { timeout: 5000 });
    
    // Trigger an error (using special test parameter)
    await page.click('[data-testid="render-button"]');
    await page.locator('[data-testid="force-error"]').click();
    
    // Verify error message appears
    const errorMessage = page.locator('[data-testid="error-message"]');
    await expect(errorMessage).toBeVisible({ timeout: 5000 });
    
    // Verify error can be dismissed
    await page.locator('[data-testid="dismiss-error"]').click();
    await expect(errorMessage).not.toBeVisible({ timeout: 2000 });
  });
});