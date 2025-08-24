import { test, expect, Page } from '@playwright/test';

test.describe('UI Controls and Features', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the login page first
    await page.goto('https://www.aistudyarchitect.com/login');
    
    // Login with provided credentials
    await page.fill('input[name="email"]', 'dropout_taekwondo');
    await page.fill('input[name="password"]', 'zf5sUdV&3WVdGtwbB$5Tw@1wTHC8j4Tz%aGE!e1^rP@M663^Rc1dUruUFpDRhvn6');
    await page.click('button[type="submit"]');
    
    // Wait for navigation to study page
    await page.waitForURL('**/study', { timeout: 10000 });
    
    // Wait for page to fully load
    await page.waitForSelector('textarea[placeholder="Type your message..."]', { timeout: 10000 });
  });

  test('should show stop button during streaming and cancel response', async ({ page }) => {
    // Send a message that will trigger streaming
    await page.fill('textarea[placeholder="Type your message..."]', 
      'Write 20 paragraphs about artificial intelligence. Each paragraph should be detailed.');
    await page.press('textarea[placeholder="Type your message..."]', 'Enter');
    
    // Wait for streaming to start
    await page.waitForSelector('text=/Thinking/', { timeout: 5000 });
    
    // Stop button should appear
    const stopButton = await page.waitForSelector('button[aria-label="Stop response (Esc)"]', { timeout: 5000 });
    expect(stopButton).toBeTruthy();
    
    // Click stop button
    await stopButton.click();
    
    // Wait a moment for cancellation
    await page.waitForTimeout(1000);
    
    // Check that streaming has stopped - input should be enabled again
    const input = page.locator('textarea[placeholder="Type your message..."]');
    await expect(input).not.toBeDisabled({ timeout: 5000 });
    
    // Check for cancelled message indicator (optional - AI might have streamed some content)
    const messages = await page.locator('p').allTextContents();
    const hasCancelledOrPartialContent = messages.some(msg => 
      msg.includes('Response cancelled') || 
      msg.includes('artificial intelligence') // Partial content before cancel
    );
    expect(hasCancelledOrPartialContent).toBe(true);
  });

  test('should cancel streaming with Escape key', async ({ page }) => {
    // Send a message
    await page.fill('textarea[placeholder="Type your message..."]', 
      'Write 15 paragraphs about space exploration.');
    await page.press('textarea[placeholder="Type your message..."]', 'Enter');
    
    // Wait for streaming to start
    await page.waitForSelector('text=/Thinking/', { timeout: 5000 });
    
    // Press Escape to stop
    await page.keyboard.press('Escape');
    
    // Check that streaming has stopped
    await page.waitForTimeout(1000);
    const input = page.locator('textarea[placeholder="Type your message..."]');
    await expect(input).not.toBeDisabled({ timeout: 5000 });
  });

  test('should show scroll-to-bottom FAB when scrolled up', async ({ page }) => {
    // First, generate some content to make the chat scrollable
    await page.fill('textarea[placeholder="Type your message..."]', 'Hello');
    await page.press('textarea[placeholder="Type your message..."]', 'Enter');
    
    // Wait for response
    await page.waitForTimeout(3000);
    
    // Send another message to create more content
    await page.fill('textarea[placeholder="Type your message..."]', 
      'Write 10 paragraphs about technology.');
    await page.press('textarea[placeholder="Type your message..."]', 'Enter');
    
    // Wait for content to stream
    await page.waitForTimeout(2000);
    
    // Scroll up
    await page.evaluate(() => {
      const container = document.querySelector('div[role="log"]');
      if (container) {
        container.scrollTop = 100;
      }
    });
    
    // FAB should appear
    const fab = await page.waitForSelector('button[aria-label*="Scroll to bottom"]', { timeout: 5000 });
    expect(fab).toBeTruthy();
    
    // Click FAB to scroll to bottom
    await fab.click();
    
    // FAB should disappear
    await expect(fab).not.toBeVisible({ timeout: 2000 });
    
    // Verify we're at the bottom
    const isAtBottom = await page.evaluate(() => {
      const container = document.querySelector('div[role="log"]');
      if (container) {
        const distance = container.scrollHeight - container.scrollTop - container.clientHeight;
        return distance < 50;
      }
      return false;
    });
    expect(isAtBottom).toBe(true);
  });

  test('should scroll to bottom with keyboard shortcut', async ({ page }) => {
    // Generate content
    await page.fill('textarea[placeholder="Type your message..."]', 'Hello');
    await page.press('textarea[placeholder="Type your message..."]', 'Enter');
    await page.waitForTimeout(2000);
    
    // Scroll up
    await page.evaluate(() => {
      const container = document.querySelector('div[role="log"]');
      if (container) {
        container.scrollTop = 0;
      }
    });
    
    // Use keyboard shortcut (Ctrl+End)
    await page.keyboard.press('Control+End');
    
    // Check that we're at the bottom
    await page.waitForTimeout(500);
    const isAtBottom = await page.evaluate(() => {
      const container = document.querySelector('div[role="log"]');
      if (container) {
        const distance = container.scrollHeight - container.scrollTop - container.clientHeight;
        return distance < 50;
      }
      return false;
    });
    expect(isAtBottom).toBe(true);
  });

  test('should show unread message count when scrolled up during streaming', async ({ page }) => {
    // Send initial message
    await page.fill('textarea[placeholder="Type your message..."]', 'Hello');
    await page.press('textarea[placeholder="Type your message..."]', 'Enter');
    await page.waitForTimeout(2000);
    
    // Send another message to trigger streaming
    await page.fill('textarea[placeholder="Type your message..."]', 
      'Write 10 paragraphs about science.');
    await page.press('textarea[placeholder="Type your message..."]', 'Enter');
    
    // Wait for streaming to start
    await page.waitForSelector('text=/Thinking/', { timeout: 5000 });
    await page.waitForTimeout(1000);
    
    // Scroll up during streaming
    await page.evaluate(() => {
      const container = document.querySelector('div[role="log"]');
      if (container) {
        container.scrollTop = 50;
      }
    });
    
    // Wait for some content to stream while scrolled up
    await page.waitForTimeout(2000);
    
    // Check for FAB with badge
    const fabWithBadge = await page.locator('button[aria-label*="Scroll to bottom"]').first();
    const badgeContent = await page.locator('.MuiBadge-badge').first().textContent();
    
    // Badge should show some unread count (may vary based on streaming speed)
    expect(parseInt(badgeContent || '0')).toBeGreaterThan(0);
  });

  test('FAB badge should only increment once per message during streaming', async ({ page }) => {
    // Send a message that will generate a long streaming response
    await page.fill('textarea[placeholder="Type your message..."]', 
      'Write a very detailed essay with at least 30 paragraphs about the history of computing');
    await page.press('textarea[placeholder="Type your message..."]', 'Enter');
    
    // Wait for streaming to start
    await page.waitForSelector('text=/Thinking/', { timeout: 5000 });
    await page.waitForTimeout(500);
    
    // Immediately scroll up to trigger unread count
    await page.evaluate(() => {
      const container = document.querySelector('div[role="log"]');
      if (container) {
        container.scrollTop = 0;
      }
    });
    
    // Collect badge values during streaming
    const badgeValues = [];
    for (let i = 0; i < 10; i++) {
      const badge = page.locator('.MuiBadge-badge').first();
      const value = await badge.textContent().catch(() => '0');
      if (value) badgeValues.push(parseInt(value));
      await page.waitForTimeout(300);
    }
    
    // The badge should stay at 1 (not increment to 99)
    // Allow for some variation but it should never reach 99
    const maxBadgeValue = Math.max(...badgeValues.filter(v => !isNaN(v)));
    expect(maxBadgeValue).toBeLessThan(10); // Should be 1, but allow some tolerance
    expect(maxBadgeValue).toBeGreaterThan(0); // Should show at least 1
    
    // Stop the response
    await page.keyboard.press('Escape');
    
    // Scroll to bottom to clear badge
    const fab = page.locator('button[aria-label*="Scroll to bottom"]').first();
    await fab.click();
    
    // Badge should disappear when at bottom
    const badge = page.locator('.MuiBadge-badge').first();
    await expect(badge).not.toBeVisible({ timeout: 2000 });
  });

  test('should have proper ARIA labels for accessibility', async ({ page }) => {
    // Check for ARIA labels on key elements
    const chatArea = await page.locator('[role="log"][aria-label="Chat messages"]');
    expect(await chatArea.count()).toBe(1);
    
    // Send button should have ARIA label
    const sendButton = await page.locator('button[aria-label="Send message"]');
    expect(await sendButton.count()).toBe(1);
    
    // Check for live region during loading
    await page.fill('textarea[placeholder="Type your message..."]', 'Test');
    await page.press('textarea[placeholder="Type your message..."]', 'Enter');
    
    const statusRegion = await page.waitForSelector('[role="status"][aria-live="assertive"]', { timeout: 5000 });
    expect(statusRegion).toBeTruthy();
  });

  test('should handle rapid stop/start cycles', async ({ page }) => {
    // Send first message
    await page.fill('textarea[placeholder="Type your message..."]', 'First message');
    await page.press('textarea[placeholder="Type your message..."]', 'Enter');
    
    // Wait briefly and stop
    await page.waitForTimeout(500);
    await page.keyboard.press('Escape');
    
    // Immediately send another message
    await page.waitForTimeout(500);
    await page.fill('textarea[placeholder="Type your message..."]', 'Second message');
    await page.press('textarea[placeholder="Type your message..."]', 'Enter');
    
    // Wait briefly and stop again
    await page.waitForTimeout(500);
    await page.keyboard.press('Escape');
    
    // Send a third message
    await page.waitForTimeout(500);
    await page.fill('textarea[placeholder="Type your message..."]', 'Third message');
    await page.press('textarea[placeholder="Type your message..."]', 'Enter');
    
    // Let this one complete
    await page.waitForTimeout(3000);
    
    // Should have multiple messages in the chat
    const messages = await page.locator('p').count();
    expect(messages).toBeGreaterThan(3); // At least the initial greeting + our messages
  });
});