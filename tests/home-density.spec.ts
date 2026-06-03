import { expect, test, type Page } from '@playwright/test';

async function metricBox(page: Page, selector: string) {
  const node = page.locator(selector).first();
  await expect(node).toBeVisible();
  return node.evaluate((element) => {
    const rect = element.getBoundingClientRect();
    const children = Array.from(element.children).map((child) => child.getBoundingClientRect());
    const maxRight = Math.max(...children.map((child) => child.right), rect.right);
    const minLeft = Math.min(...children.map((child) => child.left), rect.left);
    return {
      width: rect.width,
      usedWidth: maxRight - minLeft,
      childCount: children.length,
    };
  });
}

test('homepage uses desktop width as a product dashboard', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 1200 });
  await page.goto('http://localhost:8081/');
  await page.waitForTimeout(800);

  const hero = page.locator('.public-hero-v4').first();
  await expect(hero).toBeVisible();
  const heroMetrics = await hero.evaluate((node) => {
    const rect = node.getBoundingClientRect();
    const children = Array.from(node.children).map((child) => child.getBoundingClientRect());
    const maxRight = Math.max(...children.map((child) => child.right), rect.right);
    const minLeft = Math.min(...children.map((child) => child.left), rect.left);
    return {
      width: rect.width,
      usedWidth: maxRight - minLeft,
      childCount: children.length,
    };
  });

  expect(heroMetrics.usedWidth / heroMetrics.width).toBeGreaterThan(0.8);
  expect(heroMetrics.childCount).toBe(2);

  const layout = page.locator('.public-layout-v4').first();
  await expect(layout).toBeVisible();
  const layoutMetrics = await layout.evaluate((node) => {
    const rect = node.getBoundingClientRect();
    const children = Array.from(node.children).map((child) => child.getBoundingClientRect());
    const maxRight = Math.max(...children.map((child) => child.right), rect.right);
    const minLeft = Math.min(...children.map((child) => child.left), rect.left);
    const usedWidth = maxRight - minLeft;
    return { width: rect.width, usedWidth, childCount: children.length };
  });

  expect(layoutMetrics.usedWidth / layoutMetrics.width).toBeGreaterThan(0.85);
  expect(layoutMetrics.childCount).toBe(2);

  const statGrid = page.locator('.public-stat-grid').first();
  await expect(statGrid).toBeVisible();
  const statMetrics = await statGrid.evaluate((node) => {
    const rect = node.getBoundingClientRect();
    const cards = Array.from(node.querySelectorAll('.public-stat-card')).map((child) => child.getBoundingClientRect());
    const maxRight = Math.max(...cards.map((child) => child.right), rect.right);
    const minLeft = Math.min(...cards.map((child) => child.left), rect.left);
    return {
      width: rect.width,
      usedWidth: maxRight - minLeft,
      cardCount: cards.length,
    };
  });

  expect(statMetrics.cardCount).toBe(4);
  expect(statMetrics.usedWidth / statMetrics.width).toBeGreaterThan(0.9);

  const cards = await page.locator('.public-card-grid').count();
  expect(cards).toBeGreaterThanOrEqual(3);

  const firstCardGrid = page.locator('.public-card-grid').first();
  const cardMetrics = await metricBox(page, '.public-card-grid');
  expect(cardMetrics.usedWidth / cardMetrics.width).toBeGreaterThan(0.85);
});
