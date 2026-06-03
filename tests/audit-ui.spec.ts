import { test, expect } from '@playwright/test';

test('audit admin panel tabs', async ({ page }) => {
  // 1. Login
  console.log('Navigating to login...');
  await page.goto('http://localhost:8081/login');
  await page.screenshot({ path: 'audit_login_page.png' });
  
  await page.fill('input[type="email"]', 'admin@local.test');
  await page.fill('input[type="password"]', 'ChangeMe123!');
  console.log('Submitting login...');
  await page.click('.login-submit');

  // Wait for redirect to admin
  try {
    await page.waitForURL('**/admin', { timeout: 5000 });
    console.log('Redirected to admin');
  } catch (e) {
    console.log('Redirect to /admin failed or timed out. Current URL:', page.url());
    await page.screenshot({ path: 'audit_login_failure.png' });
    const content = await page.content();
    console.log('Page content snippet:', content.substring(0, 500));
    return;
  }

  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: 'audit_landing.png', fullPage: true });

  const tabs = [
    { name: 'overview', label: 'Overview' },
    { name: 'system-monitoring', label: 'Monitoring' }, // Shortened labels might match better
    { name: 'user-directory', label: 'Users' },
    { name: 'groups-catalog', label: 'Groups' },
    { name: 'publications-review', label: 'Publications' },
    { name: 'audit-trail', label: 'Audit' },
    { name: 'api-logs', label: 'Logs' }
  ];

  for (const tab of tabs) {
    // Click tab if possible or just navigate if it's a separate route (though here it's likely state-based)
    // The tabs are buttons in the topbar or sidebar.
    // Let's try clicking by text.
    try {
      const tabButton = page.locator(`.admin-nav-item:has-text("${tab.label}")`).or(page.locator(`.admin-top-tab:has-text("${tab.label}")`));
      if (await tabButton.count() > 0) {
          await tabButton.first().click();
          await page.waitForTimeout(1000); // Wait for transition
          await page.screenshot({ path: `audit_${tab.name}.png`, fullPage: true });
          console.log(`Captured ${tab.name}`);
      } else {
          console.log(`Tab ${tab.label} not found directly, trying to find in menu`);
      }
    } catch (e) {
      console.log(`Error capturing ${tab.name}: ${e.message}`);
    }
  }
});
