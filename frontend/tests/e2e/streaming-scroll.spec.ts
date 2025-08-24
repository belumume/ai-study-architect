import { test, expect, Page } from '@playwright/test';

test.describe('Streaming Response Scroll Behavior', () => {
  let scrollMetrics: {
    totalScrollEvents: number;
    jitterCount: number;
    largeJumps: number;
    maxDelta: number;
    scrollPositions: number[];
  };

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
    
    // Initialize scroll metrics
    scrollMetrics = {
      totalScrollEvents: 0,
      jitterCount: 0,
      largeJumps: 0,
      maxDelta: 0,
      scrollPositions: []
    };
    
    // Inject scroll monitoring script
    await page.evaluate(() => {
      window['scrollMonitor'] = {
        events: [],
        lastPosition: 0,
        
        init: function() {
          const container = document.querySelector('div[style*="overflow: auto"]');
          if (!container) return;
          
          container.addEventListener('scroll', (e) => {
            const currentPosition = container.scrollTop;
            const delta = Math.abs(currentPosition - this.lastPosition);
            
            this.events.push({
              position: currentPosition,
              delta: delta,
              timestamp: Date.now(),
              height: container.scrollHeight
            });
            
            this.lastPosition = currentPosition;
          });
        },
        
        getMetrics: function() {
          const deltas = this.events.map(e => e.delta).filter(d => d > 0);
          const jitter = deltas.filter(d => d > 0 && d < 5).length;
          const jumps = deltas.filter(d => d > 100).length;
          
          return {
            totalScrollEvents: this.events.length,
            jitterCount: jitter,
            largeJumps: jumps,
            maxDelta: Math.max(...deltas, 0),
            scrollPositions: this.events.map(e => e.position)
          };
        }
      };
      
      window['scrollMonitor'].init();
    });
  });

  test('should not vibrate or shake during streaming', async ({ page }) => {
    // Start monitoring
    await page.evaluate(() => window['scrollMonitor'].events = []);
    
    // Trigger a streaming response
    await page.fill('textarea[placeholder="Type your message..."]', 
      'Write a long detailed explanation about artificial intelligence, machine learning, and deep learning. Include multiple paragraphs with examples.');
    await page.press('textarea[placeholder="Type your message..."]', 'Enter');
    
    // Wait for streaming to start
    await page.waitForSelector('text=/Thinking/', { timeout: 5000 });
    
    // Wait for streaming to complete (or timeout after 10 seconds)
    await page.waitForFunction(
      () => {
        const input = document.querySelector('textarea[placeholder="Type your message..."]');
        return input && !input.hasAttribute('disabled');
      },
      { timeout: 10000 }
    ).catch(() => {}); // Continue even if timeout
    
    // Collect metrics
    const metrics = await page.evaluate(() => window['scrollMonitor'].getMetrics());
    
    // Assertions
    expect(metrics.jitterCount).toBeLessThan(5); // Should have minimal jitter
    expect(metrics.largeJumps).toBeLessThan(3); // Should not have many large jumps
    expect(metrics.maxDelta).toBeLessThan(200); // No huge jumps
    
    // Check for smooth progression (no back-and-forth)
    const positions = metrics.scrollPositions;
    let reversals = 0;
    for (let i = 1; i < positions.length - 1; i++) {
      if ((positions[i] > positions[i-1] && positions[i] > positions[i+1]) ||
          (positions[i] < positions[i-1] && positions[i] < positions[i+1])) {
        reversals++;
      }
    }
    expect(reversals).toBeLessThan(2); // Should have minimal direction changes
  });

  test('should respect user scroll during streaming', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    
    // Trigger a long streaming response
    await page.fill('textarea[placeholder="Type your message..."]', 
      'Write 15 paragraphs about the history of mathematics. Each paragraph should be at least 4 sentences long.');
    await page.press('textarea[placeholder="Type your message..."]', 'Enter');
    
    // Wait for streaming to start
    await page.waitForSelector('text=/Thinking/', { timeout: 5000 });
    
    // Wait for some content to stream
    await page.waitForTimeout(1500);
    
    // Find the correct scroll container and scroll up
    const scrolledUp = await page.evaluate(() => {
      // Find the messages container
      const containers = Array.from(document.querySelectorAll('div')).filter(el => {
        const style = getComputedStyle(el);
        return style.overflow === 'auto' || style.overflowY === 'auto';
      });
      
      // Find the main chat container (not the sidebar)
      const chatContainer = containers.find(c => c.scrollHeight > 500 && c.querySelector('[role="assistant"]'));
      
      if (chatContainer) {
        // Store initial position
        const initialScroll = chatContainer.scrollTop;
        // Scroll up significantly
        chatContainer.scrollTop = 100;
        // Trigger scroll event
        chatContainer.dispatchEvent(new Event('scroll', { bubbles: true }));
        return {
          found: true,
          initialScroll,
          newScroll: 100,
          scrollHeight: chatContainer.scrollHeight
        };
      }
      return { found: false };
    });
    
    expect(scrolledUp.found).toBe(true);
    
    // Monitor scroll position during streaming
    const positions = [];
    for (let i = 0; i < 5; i++) {
      await page.waitForTimeout(500);
      const pos = await page.evaluate(() => {
        const containers = Array.from(document.querySelectorAll('div')).filter(el => {
          const style = getComputedStyle(el);
          return style.overflow === 'auto' || style.overflowY === 'auto';
        });
        const chatContainer = containers.find(c => c.scrollHeight > 500 && c.querySelector('[role="assistant"]'));
        return chatContainer ? chatContainer.scrollTop : -1;
      });
      positions.push(pos);
    }
    
    // Check that scroll position stayed relatively stable (not forced to bottom)
    const maxPosition = Math.max(...positions);
    const minPosition = Math.min(...positions);
    
    // Should not jump to bottom (which would be much higher)
    expect(maxPosition).toBeLessThan(500);
    // Some variation is ok due to content, but not huge jumps
    expect(maxPosition - minPosition).toBeLessThan(200);
  });

  test('should handle rapid message sending smoothly', async ({ page }) => {
    // Send multiple messages quickly
    const messages = [
      'What is AI?',
      'Explain machine learning',
      'What about deep learning?'
    ];
    
    for (const message of messages) {
      await page.fill('textarea[placeholder="Type your message..."]', message);
      await page.press('textarea[placeholder="Type your message..."]', 'Enter');
      await page.waitForTimeout(500); // Small delay between messages
    }
    
    // Wait for all responses
    await page.waitForTimeout(5000);
    
    // Get final metrics
    const metrics = await page.evaluate(() => window['scrollMonitor'].getMetrics());
    
    // Should handle multiple messages without excessive jitter
    expect(metrics.jitterCount / metrics.totalScrollEvents).toBeLessThan(0.2); // Less than 20% jitter
  });

  test('should perform well on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 390, height: 844 });
    
    // Reset scroll monitor for mobile
    await page.evaluate(() => {
      window['scrollMonitor'].events = [];
      window['scrollMonitor'].lastPosition = 0;
    });
    
    // Trigger streaming on mobile
    await page.fill('textarea[placeholder="Type your message..."]', 
      'Explain the water cycle in detail');
    await page.press('textarea[placeholder="Type your message..."]', 'Enter');
    
    // Wait for response
    await page.waitForTimeout(5000);
    
    // Get mobile metrics
    const metrics = await page.evaluate(() => window['scrollMonitor'].getMetrics());
    
    // Mobile should also have smooth scrolling
    expect(metrics.jitterCount).toBeLessThan(10); // Slightly more tolerance for mobile
    expect(metrics.maxDelta).toBeLessThan(150); // Smaller jumps on mobile
  });

  test('should maintain performance over long conversations', async ({ page }) => {
    // Simulate a longer conversation
    const messages = Array(5).fill(null).map((_, i) => `Test message ${i + 1}`);
    
    for (const message of messages) {
      await page.fill('textarea[placeholder="Type your message..."]', message);
      await page.press('textarea[placeholder="Type your message..."]', 'Enter');
      
      // Wait for response
      await page.waitForFunction(
        () => !document.querySelector('textarea[placeholder="Type your message..."]').hasAttribute('disabled'),
        { timeout: 10000 }
      );
    }
    
    // Get performance metrics
    const metrics = await page.evaluate(() => {
      const monitor = window['scrollMonitor'];
      const events = monitor.events;
      
      // Calculate average time between scroll events
      let totalTime = 0;
      for (let i = 1; i < events.length; i++) {
        totalTime += events[i].timestamp - events[i-1].timestamp;
      }
      const avgTimeBetweenScrolls = totalTime / (events.length - 1);
      
      return {
        ...monitor.getMetrics(),
        avgTimeBetweenScrolls
      };
    });
    
    // Performance should remain consistent
    expect(metrics.avgTimeBetweenScrolls).toBeGreaterThan(50); // Not too frequent
    expect(metrics.avgTimeBetweenScrolls).toBeLessThan(500); // Not too sparse
  });
});

// Performance benchmark test
test.describe('Scroll Performance Benchmarks', () => {
  test('should meet performance thresholds', async ({ page }) => {
    await page.goto('https://www.aistudyarchitect.com/study');
    
    // Measure scroll performance
    const performanceMetrics = await page.evaluate(async () => {
      return new Promise((resolve) => {
        const metrics = {
          paintTimes: [],
          scrollDelays: [],
          frameDrops: 0
        };
        
        let lastPaintTime = performance.now();
        let frameCount = 0;
        
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.entryType === 'paint') {
              metrics.paintTimes.push(entry.startTime);
            }
          }
        });
        
        observer.observe({ entryTypes: ['paint'] });
        
        // Monitor for 3 seconds
        const checkFrame = () => {
          const now = performance.now();
          const delta = now - lastPaintTime;
          
          if (delta > 33) { // More than 2 frames at 60fps
            metrics.frameDrops++;
          }
          
          lastPaintTime = now;
          frameCount++;
          
          if (frameCount < 180) { // 3 seconds at 60fps
            requestAnimationFrame(checkFrame);
          } else {
            resolve(metrics);
          }
        };
        
        requestAnimationFrame(checkFrame);
      });
    });
    
    // Assert performance thresholds
    expect(performanceMetrics.frameDrops).toBeLessThan(10); // Less than 10 dropped frames in 3 seconds
  });
});