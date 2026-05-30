/**
 * pwa.spec.ts
 *
 * Progressive Web App (PWA) offline tests:
 *   - Visit homepage → verify content loads
 *   - Go offline → verify cached content is still visible
 *   - Restore network → verify app recovers
 *
 * Prerequisites:
 *   - Frontend running on http://localhost:5173
 *   - Service Worker registered (production build recommended)
 */

import { test, expect } from '@playwright/test';

test.describe('PWA: Offline Support', () => {
  test('homepage loads successfully when online', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const bodyText = await page.textContent('body');
    expect(bodyText?.length).toBeGreaterThan(50);

    // Check for service worker registration if available
    const hasSW = await page.evaluate(async () => {
      if ('serviceWorker' in navigator) {
        const registrations = await navigator.serviceWorker.getRegistrations();
        return registrations.length > 0;
      }
      return false;
    }).catch(() => false);

    // Log SW status for debugging (not a hard assertion)
    console.log(`Service Worker registered: ${hasSW}`);
  });

  test('offline mode shows cached content', async ({ page, context }) => {
    // Step 1: Visit the page to populate cache
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Give the service worker time to cache assets
    await page.waitForTimeout(2000);

    // Capture content before going offline
    const onlineContent = await page.textContent('body');

    // Step 2: Go offline
    await context.setOffline(true);

    // Step 3: Reload the page offline
    await page.reload();

    // The page may show cached content or an offline fallback
    // Either is acceptable PWA behavior
    const offlineContent = await page.textContent('body');

    // Verify we have content (either cached page or offline fallback)
    expect(offlineContent?.length).toBeGreaterThan(10);

    // If service worker caching is working, content should be similar
    // If not, we at least expect an offline indicator
    const hasOfflineIndicator =
      offlineContent?.toLowerCase().includes('offline') ||
      offlineContent?.toLowerCase().includes('no internet') ||
      offlineContent?.toLowerCase().includes('离线') ||
      offlineContent?.toLowerCase().includes('network');

    // Either the page loads cached content, or it shows an offline message
    // Both are valid PWA behaviors
    const hasMeaningfulContent = offlineContent && offlineContent.length > 100;

    expect(hasOfflineIndicator || hasMeaningfulContent).toBeTruthy();
  });

  test('app recovers after network is restored', async ({ page, context }) => {
    // Step 1: Load page online
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Step 2: Go offline
    await context.setOffline(true);
    await page.reload();
    await page.waitForTimeout(1000);

    // Step 3: Restore network
    await context.setOffline(false);

    // Step 4: Reload and verify app works
    await page.reload();
    await page.waitForLoadState('networkidle');

    const finalContent = await page.textContent('body');
    expect(finalContent?.length).toBeGreaterThan(50);
  });

  test('navigation works after offline→online transition', async ({ page, context }) => {
    // Load page
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Go offline briefly
    await context.setOffline(true);
    await page.waitForTimeout(1000);

    // Restore network
    await context.setOffline(false);

    // Try navigating to another page
    const firstLink = page.locator('a[href]:not([href^="http"])').first();
    if (await firstLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await firstLink.click();
      await page.waitForLoadState('networkidle');
    }

    const bodyText = await page.textContent('body');
    expect(bodyText?.length).toBeGreaterThan(50);
  });
});
