# RFM Architecture Testing

This directory contains tests for the RFM Architecture application.

## Visual Regression Testing

The visual regression tests use Playwright to capture and compare screenshots of the application interface. This helps catch unintended visual changes between versions.

### How It Works

1. The `take_app_screenshot.py` script:
   - Launches the premium UI application
   - Takes a screenshot using DearPyGui's screenshot capability
   - Saves the screenshot to the `screenshots` directory
   - Exits the application

2. The Playwright test (`visual_regression.spec.ts`):
   - Runs the screenshot script
   - Compares the resulting image against a baseline
   - Reports any unexpected visual differences

### Running Tests

To run the visual regression tests:

```bash
# Make sure you've installed the dependencies
npm install
npx playwright install

# Run the test
npx playwright test
```

On the first run, this will create a baseline screenshot. Subsequent runs will compare against this baseline.

### Test Configuration

Test settings are configured in `playwright.config.ts`. Key settings include:

- Visual difference threshold: 20% (allows for minor rendering differences)
- Test timeout: 30 seconds (allows time for the app to launch and render)

## Notes for CI/CD

When running in CI/CD environments:

1. Make sure all required dependencies are installed:
   - Python with the application dependencies
   - Node.js and Playwright
   - Pillow for screenshot capabilities

2. The test automatically creates the screenshots directory if it doesn't exist.

3. The CI workflow will fail if the visual differences exceed the configured threshold.