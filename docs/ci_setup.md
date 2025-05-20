# CI/CD Setup for RFM Architecture

This document describes the Continuous Integration and Deployment (CI/CD) setup for the RFM Architecture project.

## Overview

The RFM Architecture project uses GitHub Actions for CI/CD, providing:

- Multi-OS builds (Windows, macOS, Linux)
- Multiple Python version testing (3.9, 3.10, 3.11)
- Automated testing with pytest
- Visual regression testing with Playwright
- Artifact creation for all platforms
- Automated executable building

## Workflow Files

The project includes the following GitHub Actions workflow files:

1. `build-premium-ui.yml` - Standard build workflow
2. `multi-os-build.yml` - Extended multi-OS, multi-Python version build workflow

## Multi-OS Build Workflow

The `multi-os-build.yml` workflow runs on:

- Windows (latest)
- macOS (latest)
- Ubuntu (latest)

And tests with Python versions:
- 3.9
- 3.10
- 3.11

### Workflow Steps

1. **Checkout code**: Get the latest code from the repository
2. **Set up Python**: Install the specified Python version
3. **Install dependencies**: 
   - Install pip packages
   - Set up Poetry
   - Install project dependencies
4. **Install Playwright**: Set up browser dependencies for visual testing
5. **Run tests**: Execute pytest test suite
6. **Visual testing**: Create screenshots and run visual regression tests
7. **Build executable**: Create standalone executable with PyInstaller
8. **Upload artifacts**: Store binaries and test results

### Configuration Options

The workflow can be customized through:

1. **Python versions**: Add or remove Python versions from the matrix
2. **OS versions**: Specify different OS versions if needed
3. **Test configuration**: Modify test commands and options
4. **Build flags**: Adjust PyInstaller options for different builds

## Build Artifacts

For each OS and Python version combination, the workflow produces:

1. **Executable**:
   - Windows: `RFM-Premium.exe`
   - macOS: `RFM-Premium`
   - Linux: `RFM-Premium`

2. **Test Results**:
   - Unit test reports
   - Visual regression test results
   - Screenshot artifacts

## Manual Triggering

The workflow can be triggered:

1. Automatically on pushes to the `main` branch
2. Automatically on pull requests to the `main` branch
3. Manually via GitHub's workflow dispatch feature

## Local Testing

To test the CI process locally before pushing:

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements_dev.txt

# Run tests
pytest -v

# Create screenshots
python tests/take_app_screenshot.py

# Run visual tests
npx playwright test

# Build executable
pyinstaller run_premium_ui.py --onefile --name RFM-Premium
```

## Troubleshooting

Common issues and solutions:

1. **Missing dependencies**:
   - Check that all dependencies are correctly listed in requirements.txt
   - Some packages may need OS-specific installation steps

2. **Visual test failures**:
   - Different OSes may render UI elements slightly differently
   - Use Playwright's update-snapshots option to create baseline images for each OS

3. **Build failures**:
   - PyInstaller may need different options for different platforms
   - Check hidden imports and data files in the PyInstaller spec file

## Future Enhancements

Planned enhancements to the CI/CD pipeline:

1. **Automated versioning** using git tags
2. **Release automation** for GitHub Releases
3. **Code coverage reporting** for test quality
4. **Static analysis** with tools like Ruff and MyPy
5. **Dependency scanning** for security vulnerabilities