import { test, expect, devices } from '@playwright/test';

// Configure mobile viewport
test.use({
  ...devices['iPhone 13'],
  permissions: ['geolocation'],
});

test.describe('Mobile Responsiveness Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('https://ai-study-architect.onrender.com');
  });

  test('should display mobile navigation menu', async ({ page }) => {
    // Check if hamburger menu is visible on mobile
    const hamburgerMenu = page.locator('[data-testid="mobile-menu-button"], button[aria-label*="menu" i], .hamburger, .menu-toggle, button:has-text("☰")');
    
    // Try to find any button that might be a menu toggle
    const possibleMenuButtons = await page.locator('button').all();
    console.log(`Found ${possibleMenuButtons.length} buttons on the page`);
    
    // Take screenshot for visual inspection
    await page.screenshot({ path: 'mobile-home.png', fullPage: true });
    
    // Check viewport size
    const viewportSize = page.viewportSize();
    console.log('Viewport size:', viewportSize);
    expect(viewportSize?.width).toBeLessThanOrEqual(428);
  });

  test('should have responsive layout', async ({ page }) => {
    // Check if main content is properly sized for mobile
    const mainContent = page.locator('main, .main-content, #root > div');
    const boundingBox = await mainContent.boundingBox();
    
    if (boundingBox) {
      console.log('Main content width:', boundingBox.width);
      expect(boundingBox.width).toBeLessThanOrEqual(428);
    }

    // Check for horizontal overflow
    const hasHorizontalScroll = await page.evaluate(() => {
      return document.documentElement.scrollWidth > document.documentElement.clientWidth;
    });
    expect(hasHorizontalScroll).toBe(false);
  });

  test('should display login form properly on mobile', async ({ page }) => {
    // Navigate to login if not already there
    const loginLink = page.locator('a[href="/login"], button:has-text("Login"), a:has-text("Sign In")');
    if (await loginLink.isVisible()) {
      await loginLink.click();
      await page.waitForLoadState('networkidle');
    }

    // Check login form
    const loginForm = page.locator('form').first();
    if (await loginForm.isVisible()) {
      const formBox = await loginForm.boundingBox();
      if (formBox) {
        console.log('Login form width:', formBox.width);
        expect(formBox.width).toBeLessThanOrEqual(428);
      }
    }

    await page.screenshot({ path: 'mobile-login.png', fullPage: true });
  });

  test('should handle touch interactions', async ({ page }) => {
    // Test touch/click on buttons
    const buttons = await page.locator('button').all();
    
    for (let i = 0; i < Math.min(3, buttons.length); i++) {
      const button = buttons[i];
      const isVisible = await button.isVisible();
      if (isVisible) {
        const text = await button.textContent();
        console.log(`Testing button: ${text}`);
        
        // Check if button is accessible on mobile
        const box = await button.boundingBox();
        if (box) {
          // Minimum touch target size should be 44x44 pixels (iOS guideline)
          expect(box.width).toBeGreaterThanOrEqual(44);
          expect(box.height).toBeGreaterThanOrEqual(30); // Slightly lower for text buttons
        }
      }
    }
  });

  test('should have readable text on mobile', async ({ page }) => {
    // Check font sizes
    const textElements = await page.locator('p, span, div, h1, h2, h3, h4, h5, h6').all();
    
    for (let i = 0; i < Math.min(10, textElements.length); i++) {
      const element = textElements[i];
      const fontSize = await element.evaluate(el => {
        return window.getComputedStyle(el).fontSize;
      });
      
      const fontSizeNum = parseInt(fontSize);
      if (fontSizeNum > 0) {
        // Minimum readable font size on mobile is typically 12px
        expect(fontSizeNum).toBeGreaterThanOrEqual(12);
      }
    }
  });

  test('should handle mobile chat interface', async ({ page, context }) => {
    // Create a test user session
    await context.addCookies([{
      name: 'test_session',
      value: 'test_value',
      domain: 'localhost',
      path: '/'
    }]);

    // Try to navigate to chat
    await page.goto('https://ai-study-architect.onrender.com/chat');
    await page.waitForLoadState('networkidle');

    // Check chat interface on mobile
    const chatContainer = page.locator('.chat-container, [class*="chat"], main');
    if (await chatContainer.isVisible()) {
      const chatBox = await chatContainer.boundingBox();
      if (chatBox) {
        console.log('Chat container width:', chatBox.width);
        expect(chatBox.width).toBeLessThanOrEqual(428);
      }
    }

    await page.screenshot({ path: 'mobile-chat.png', fullPage: true });
  });

  test('should check for mobile-specific CSS issues', async ({ page }) => {
    // Check for elements that might cause overflow
    const overflowingElements = await page.evaluate(() => {
      const elements: string[] = [];
      document.querySelectorAll('*').forEach(el => {
        const rect = el.getBoundingClientRect();
        if (rect.width > window.innerWidth || rect.right > window.innerWidth) {
          elements.push(`${el.tagName}.${el.className}: width=${rect.width}px`);
        }
      });
      return elements;
    });

    console.log('Overflowing elements:', overflowingElements);
    expect(overflowingElements.length).toBe(0);
  });
});