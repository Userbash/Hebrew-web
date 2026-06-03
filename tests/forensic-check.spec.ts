import { test, expect } from '@playwright/test';

test('forensic check', async ({ page }) => {
  page.on('console', msg => console.log('BROWSER CONSOLE:', msg.text()));

  console.log('Navigating to login...');
  await page.goto('http://localhost:8081/login');
  
  console.log('Filling login form...');
  await page.fill('input[type="email"]', 'admin@local.test');
  await page.fill('input[type="password"]', 'ChangeMe123!');
  
  const submitButton = page.locator('button[type="submit"]');
  console.log('Submit button enabled:', await submitButton.isEnabled());
  
  await submitButton.click();
  
  console.log('Waiting for network idle...');
  await page.waitForLoadState('networkidle');
  
  console.log('URL after login attempt:', page.url());

  const alert = await page.textContent('.alert-danger').catch(() => 'NO ERROR ALERT');
  console.log('LOGIN ERROR ALERT:', alert);

  await page.screenshot({ path: 'forensic_admin.png', fullPage: true });
});
