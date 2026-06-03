import { test, expect } from '@playwright/test';

test('Full Admin Panel Visual Audit', async ({ page }) => {
  await page.goto('http://localhost:8081/');
  await page.waitForTimeout(800);
  await page.screenshot({ path: 'audit_homepage_overview.png', fullPage: true });

  // Login
  await page.goto('http://localhost:8081/login');
  await page.fill('input[name="email"]', 'admin@local.test');
  await page.fill('input[name="password"]', 'ChangeMe123!');
  await page.click('button[type="submit"]');
  await page.waitForURL('**/admin');
  
  // Wait for React to mount and data to load
  await page.waitForTimeout(1000);

  // Take Overview screenshot
  await page.screenshot({ path: 'audit_final_overview.png', fullPage: true });

  // Navigate to System Monitoring
  await page.getByTestId('admin-nav-item-system-monitoring').click();
  await page.waitForTimeout(500);
  await page.screenshot({ path: 'audit_final_monitoring.png', fullPage: true });

  // Navigate to Directory
  await page.getByTestId('admin-nav-item-user-directory').click();
  await page.waitForTimeout(500);
  await page.screenshot({ path: 'audit_final_directory.png', fullPage: true });

  // Navigate to Groups Catalog
  await page.getByTestId('admin-nav-item-groups-catalog').click();
  await page.waitForTimeout(500);
  await page.screenshot({ path: 'audit_final_groups.png', fullPage: true });

  // Navigate to Audit Trail
  await page.getByTestId('admin-nav-item-audit-trail').click();
  await page.waitForTimeout(500);
  await page.screenshot({ path: 'audit_final_audittrail.png', fullPage: true });
});
