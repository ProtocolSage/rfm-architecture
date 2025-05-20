import { test, expect } from '@playwright/test';
import { execSync } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

// For desktop apps, we'll use a different approach since we can't use page.goto
test('RFM-Architecture UI snapshot test', async () => {
  const screenshotDir = path.join(process.cwd(), 'tests', 'screenshots');
  if (!fs.existsSync(screenshotDir)) {
    fs.mkdirSync(screenshotDir, { recursive: true });
  }
  
  const screenshotPath = path.join(screenshotDir, 'app_screenshot.png');
  
  try {
    // On Windows, this requires Python and the Pillow library
    // This will launch the app, take a screenshot, and exit
    console.log('Taking application screenshot...');
    
    // Execute the screenshot script with Pillow's ImageGrab
    console.log('Capturing application screenshot using Pillow ImageGrab...');
    execSync('python tests/take_app_screenshot.py', { 
      timeout: 15000,
      stdio: 'inherit'
    });
    
    // Check if screenshot was created
    if (fs.existsSync(screenshotPath)) {
      const screenshot = fs.readFileSync(screenshotPath);
      expect(screenshot).toBeTruthy();
      console.log('Screenshot captured successfully');
      
      // Visual comparison test
      // Use toMatchSnapshot for visual regression testing
      // This creates a baseline on first run and compares in subsequent runs
      expect(screenshot).toMatchSnapshot('app_ui.png');
    } else {
      throw new Error('Screenshot not created');
    }
  } catch (error) {
    console.error('Error during test:', error);
    throw error;
  }
});