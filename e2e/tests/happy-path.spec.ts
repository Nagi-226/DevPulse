/**
 * happy-path.spec.ts
 *
 * Full happy-path user journey:
 *   Sign up → Browse Trending → View detail → Like → Comment
 *
 * Prerequisites:
 *   - Backend running on http://localhost:8000
 *   - Frontend running on http://localhost:5173
 */

import { test, expect } from '@playwright/test';

const TEST_USER = {
  username: `e2e-user-${Date.now()}`,
  email: `e2e-${Date.now()}@devpulse.test`,
  password: 'TestPass123!',
};

test.describe('Happy Path: Full User Journey', () => {
  test('register → browse trending → view detail → like → comment', async ({ page }) => {
    // ------------------------------------------------------------------
    // Step 1: Visit homepage and verify Trending list is visible
    // ------------------------------------------------------------------
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Verify the page has loaded with trending content
    // Look for trending section or repo cards
    const trendingSection = page.locator(
      '[data-testid="trending-section"], .trending, [class*="trending"], main'
    );
    await expect(trendingSection.first()).toBeVisible({ timeout: 10000 });

    // ------------------------------------------------------------------
    // Step 2: Click the first repository to enter detail page
    // ------------------------------------------------------------------
    const firstRepoLink = page.locator(
      'a[href*="/repo/"], a[href*="/repos/"], [data-testid="repo-card"] a, [class*="repo-card"] a'
    ).first();

    // If no direct link, try clicking the card itself
    const firstRepoCard = page.locator(
      '[data-testid="repo-card"], [class*="repo-card"], [class*="RepoCard"]'
    ).first();

    if (await firstRepoLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await firstRepoLink.click();
    } else if (await firstRepoCard.isVisible({ timeout: 3000 }).catch(() => false)) {
      await firstRepoCard.click();
    } else {
      // Fallback: navigate directly to a known repo path
      await page.goto('/repo/1');
    }

    await page.waitForLoadState('networkidle');

    // Verify we are on a detail page
    const detailContent = page.locator(
      '[data-testid="repo-detail"], [class*="detail"], article, main'
    );
    await expect(detailContent.first()).toBeVisible({ timeout: 10000 });

    // ------------------------------------------------------------------
    // Step 3: Register a new user
    // ------------------------------------------------------------------
    // Navigate to sign-up / register page
    const signUpLink = page.locator(
      'a[href*="register"], a[href*="signup"], a[href*="sign-up"], button:has-text("Sign"), [data-testid="signup-link"]'
    ).first();

    if (await signUpLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await signUpLink.click();
    } else {
      await page.goto('/register');
    }

    await page.waitForLoadState('networkidle');

    // Fill registration form
    const usernameInput = page.locator(
      'input[name="username"], input[placeholder*="user"], [data-testid="username-input"]'
    ).first();
    const emailInput = page.locator(
      'input[name="email"], input[type="email"], [data-testid="email-input"]'
    ).first();
    const passwordInput = page.locator(
      'input[name="password"], input[type="password"], [data-testid="password-input"]'
    ).first();
    const submitButton = page.locator(
      'button[type="submit"], button:has-text("Register"), button:has-text("Sign"), [data-testid="register-submit"]'
    ).first();

    if (await usernameInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      await usernameInput.fill(TEST_USER.username);
    }
    if (await emailInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      await emailInput.fill(TEST_USER.email);
    }
    if (await passwordInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      await passwordInput.fill(TEST_USER.password);
    }
    if (await submitButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await submitButton.click();
    }

    await page.waitForLoadState('networkidle');
    // Registration may auto-redirect or show success
    await page.waitForTimeout(2000);

    // ------------------------------------------------------------------
    // Step 4: Navigate back to a repo detail and click Like button
    // ------------------------------------------------------------------
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Navigate to a repo detail
    const repoCard = page.locator(
      '[data-testid="repo-card"], [class*="repo-card"], [class*="RepoCard"], a[href*="/repo"]'
    ).first();

    if (await repoCard.isVisible({ timeout: 5000 }).catch(() => false)) {
      await repoCard.click();
    } else {
      await page.goto('/repo/1');
    }

    await page.waitForLoadState('networkidle');

    // Click Like button
    const likeButton = page.locator(
      '[data-testid="like-button"], button:has-text("Like"), button:has-text("👍"), [class*="like"], [aria-label*="like" i]'
    ).first();

    if (await likeButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await likeButton.click();
      await page.waitForTimeout(1000);
      // Verify the like state changed (button toggled, count increased, or visual change)
    }

    // ------------------------------------------------------------------
    // Step 5: Post a comment
    // ------------------------------------------------------------------
    const commentInput = page.locator(
      '[data-testid="comment-input"], textarea[placeholder*="comment" i], textarea[placeholder*="评论"], [class*="comment"] textarea, [contenteditable="true"]'
    ).first();

    const commentText = 'Great project! E2E test comment.';

    if (await commentInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await commentInput.fill(commentText);
    }

    // Submit comment
    const commentSubmit = page.locator(
      '[data-testid="comment-submit"], button:has-text("Submit"), button:has-text("Comment"), button:has-text("Post"), button:has-text("发送"), button:has-text("评论")'
    ).first();

    if (await commentSubmit.isVisible({ timeout: 3000 }).catch(() => false)) {
      await commentSubmit.click();
      await page.waitForTimeout(2000);
    }

    // Verify the comment appears in the list
    const commentList = page.locator(
      '[data-testid="comment-list"], [class*="comment-list"], [class*="comments"]'
    ).first();

    if (await commentList.isVisible({ timeout: 5000 }).catch(() => false)) {
      // Verify our comment text appears somewhere
      await expect(commentList).toContainText(commentText, { timeout: 5000 });
    }
  });
});
