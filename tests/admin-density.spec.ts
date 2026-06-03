import { expect, test, type Page } from '@playwright/test';

async function login(page: Page) {
  await page.goto('http://localhost:8081/login');
  await page.fill('input[name="email"]', 'admin@local.test');
  await page.fill('input[name="password"]', 'ChangeMe123!');
  await page.click('button[type="submit"]');
  await page.waitForURL('**/admin');
  await page.waitForTimeout(800);
}

async function expectDenseGrid(page: Page, navTestId: string) {
  await page.getByTestId(navTestId).click();
  await page.waitForTimeout(500);

  const formGrid = page.locator('.admin-form-grid').first();
  await expect(formGrid).toBeVisible();

  const formMetrics = await formGrid.evaluate((node) => {
    const rect = node.getBoundingClientRect();
    const children = Array.from(node.children).map((child) => child.getBoundingClientRect());
    const uniqueRows = new Set(children.map((child) => Math.round(child.top))).size;
    const maxRight = Math.max(...children.map((child) => child.right));
    const minLeft = Math.min(...children.map((child) => child.left));
    return {
      width: rect.width,
      usedWidth: maxRight - minLeft,
      uniqueRows,
      childCount: children.length,
    };
  });

  expect(formMetrics.usedWidth / formMetrics.width).toBeGreaterThan(0.75);
  expect(formMetrics.uniqueRows).toBeLessThanOrEqual(2);
  expect(formMetrics.childCount).toBeGreaterThanOrEqual(5);

  const kpiGrid = page.locator('.admin-kpi-grid').first();
  await expect(kpiGrid).toBeVisible();

  const kpiMetrics = await kpiGrid.evaluate((node) => {
    const rect = node.getBoundingClientRect();
    const cards = Array.from(node.querySelectorAll('.admin-kpi')).map((card) => card.getBoundingClientRect());
    const widest = Math.max(...cards.map((card) => card.width));
    const usedWidth = Math.max(...cards.map((card) => card.right)) - Math.min(...cards.map((card) => card.left));
    return { width: rect.width, usedWidth, widest, cardCount: cards.length };
  });

  expect(kpiMetrics.cardCount).toBeGreaterThanOrEqual(3);
  expect(kpiMetrics.usedWidth / kpiMetrics.width).toBeGreaterThan(0.5);
  expect(kpiMetrics.widest).toBeLessThan(360);
}


async function expectPublicationFormDensity(page: Page) {
  await page.getByTestId('admin-nav-item-publications-review').click();
  await page.waitForTimeout(500);

  const formGrid = page.locator('.admin-publication-form-grid').first();
  await expect(formGrid).toBeVisible();

  const metrics = await formGrid.evaluate((node) => {
    const rect = node.getBoundingClientRect();
    const children = Array.from(node.children).map((child) => child.getBoundingClientRect());
    const uniqueRows = new Set(children.map((child) => Math.round(child.top))).size;
    const maxRight = Math.max(...children.map((child) => child.right));
    const minLeft = Math.min(...children.map((child) => child.left));
    const widest = Math.max(...children.map((child) => child.width));
    return {
      width: rect.width,
      usedWidth: maxRight - minLeft,
      uniqueRows,
      childCount: children.length,
      widest,
    };
  });

  expect(metrics.childCount).toBeGreaterThanOrEqual(5);
  expect(metrics.usedWidth / metrics.width).toBeGreaterThan(0.8);
  expect(metrics.uniqueRows).toBeLessThanOrEqual(3);
  expect(metrics.widest / metrics.width).toBeGreaterThan(0.45);
}

test('admin audit and log pages use desktop width efficiently', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await login(page);
  await expectPublicationFormDensity(page);
  await expectDenseGrid(page, 'admin-nav-item-audit-trail');
  await expectDenseGrid(page, 'admin-nav-item-audit-logs');
});
