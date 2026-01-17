# VS Code Setup Guide for DREDGE-Cli

This guide will help you clone and set up the DREDGE-Cli repository in Visual Studio Code.

## Prerequisites

Before cloning, ensure you have the following installed:

1. **Git** - [Download Git](https://git-scm.com/downloads)
2. **Python 3.9-3.12** - [Download Python](https://www.python.org/downloads/)
3. **Visual Studio Code** - [Download VS Code](https://code.visualstudio.com/)
4. **Swift (optional, for Swift development)** - [Install Swift](https://www.swift.org/install/)

## Cloning the Repository in VS Code

### Method 1: Using VS Code Command Palette

1. Open Visual Studio Code
2. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac) to open the Command Palette
3. Type "Git: Clone" and select it
4. Enter the repository URL:
   ```
   https://github.com/QueenFi703/DREDGE-Cli.git
   ```
5. Choose a folder location where you want to clone the repository
6. Click "Open" when prompted to open the cloned repository

### Method 2: Using Terminal in VS Code

1. Open Visual Studio Code
2. Open the integrated terminal: `Ctrl+` ` (Windows/Linux) or `Cmd+` ` (Mac)
3. Navigate to your desired directory:
   ```bash
   cd ~/projects
   ```
4. Clone the repository:
   ```bash
   git clone https://github.com/QueenFi703/DREDGE-Cli.git
   ```
5. Open the folder in VS Code:
   ```bash
   code DREDGE-Cli
   ```

### Method 3: Using GitHub in VS Code

1. Install the "GitHub Pull Requests and Issues" extension
2. Sign in to GitHub from VS Code
3. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
4. Type "GitHub: Clone" and select it
5. Search for "QueenFi703/DREDGE-Cli"
6. Select the repository and choose a location

## Initial Setup After Cloning

### 1. Install Recommended Extensions

When you first open the repository, VS Code will prompt you to install recommended extensions. Click "Install" or manually install:

- **Python** - Microsoft's Python extension
- **Pylance** - Python language server
- **Black Formatter** - Python code formatter
- **Swift** - Swift language support (optional)
- **GitHub Copilot** - AI-powered code completion (optional)

### 2. Set Up Python Environment

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Activate the virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - **Windows (Command Prompt)**:
     ```cmd
     .venv\Scripts\activate.bat
     ```
   - **macOS/Linux**:
     ```bash
     source .venv/bin/activate
     ```

3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

4. Install development dependencies:
   ```bash
   pip install pytest torch flask numpy matplotlib
   ```

### 3. Verify Python Setup

1. Open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
2. Type "Python: Select Interpreter"
3. Choose the interpreter from `.venv` folder

### 4. Set Up Swift (Optional)

If you want to work with Swift components:

1. Ensure Swift is installed on your system
2. Open a terminal and verify:
   ```bash
   swift --version
   ```
3. Build the Swift package:
   ```bash
   swift build
   ```

## Running the Application

### From VS Code Tasks

Press `Ctrl+Shift+P` (or `Cmd+Shift+P`), type "Tasks: Run Task", and select:

- **Start DREDGE Server** - Start the DREDGE x Dolly server on port 3001
- **Start MCP Server** - Start the MCP server on port 3002
- **Run Python Tests** - Run all Python tests
- **Run Swift Tests** - Run all Swift tests
- **Build Swift Package** - Build the Swift CLI

### From Integrated Terminal

1. **DREDGE Server**:
   ```bash
   python -m dredge serve --host 0.0.0.0 --port 3001 --debug
   ```

2. **MCP Server** (with String Theory):
   ```bash
   python -m dredge mcp --host 0.0.0.0 --port 3002 --debug
   ```

3. **Swift CLI**:
   ```bash
   swift run dredge-cli
   ```

## Testing

### Running Python Tests

1. **All tests**:
   ```bash
   pytest
   ```

2. **Specific test file**:
   ```bash
   pytest tests/test_string_theory.py -v
   ```

3. **Using VS Code Test Explorer**:
   - Click the beaker icon in the sidebar
   - Click "Configure Python Tests"
   - Select "pytest"
   - Tests will appear in the Test Explorer

### Running Swift Tests

```bash
swift test
```

Or use the VS Code task: `Tasks: Run Task` → `Run Swift Tests`

## Debugging

### Python Debugging

1. Set breakpoints by clicking in the gutter next to line numbers
2. Press `F5` or go to Run → Start Debugging
3. Select a debug configuration:
   - **Python: DREDGE Server** - Debug the DREDGE server
   - **Python: MCP Server** - Debug the MCP server
   - **Python: Current Test File** - Debug the current test file

### Quick Tips

- `F9` - Toggle breakpoint
- `F5` - Start/Continue debugging
- `F10` - Step over
- `F11` - Step into
- `Shift+F11` - Step out

## Working with Git in VS Code

### Source Control Panel

1. Click the Source Control icon in the sidebar (or press `Ctrl+Shift+G`)
2. View changed files
3. Stage changes by clicking the `+` icon
4. Write a commit message
5. Click the checkmark to commit

### Common Git Commands in Terminal

```bash
# Check status
git status

# Create a new branch
git checkout -b feature/my-feature

# Stage changes
git add .

# Commit changes
git commit -m "Description of changes"

# Push changes
git push origin feature/my-feature

# Pull latest changes
git pull origin main
```

## Port Forwarding (for Remote Development)

If you're using VS Code Remote Development or GitHub Codespaces:

1. The `.devcontainer` configuration automatically forwards ports 3001 and 3002
2. You can access servers at:
   - DREDGE Server: `http://localhost:3001`
   - MCP Server: `http://localhost:3002`

## Troubleshooting

### Python Virtual Environment Not Activating

- Ensure you've selected the correct Python interpreter in VS Code
- Try creating a new virtual environment: `python -m venv .venv`

### Import Errors

- Make sure you've installed the package: `pip install -e .`
- Verify the virtual environment is activated

### Swift Build Errors

- Check Swift version: `swift --version` (requires Swift 5.9+)
- Clean build: `swift package clean`

### Port Already in Use

- Check if another process is using the port: `lsof -i :3001` (macOS/Linux)
- Stop the process or use a different port with `--port` flag

## Features Available in VS Code

- **IntelliSense** - Autocomplete for Python and Swift
- **Integrated Terminal** - Run commands without leaving VS Code
- **Git Integration** - Stage, commit, and push from the GUI
- **Debug Console** - Interactive debugging with REPL
- **Test Explorer** - Run and debug tests visually
- **Tasks** - Predefined tasks for common operations
- **Extensions** - Enhance functionality with extensions

## Additional Resources

- [README.md](../README.md) - Main project documentation
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [SWIFT_PACKAGE_GUIDE.md](../SWIFT_PACKAGE_GUIDE.md) - Swift development guide
- [VS Code Python Tutorial](https://code.visualstudio.com/docs/python/python-tutorial)
- [VS Code Git Tutorial](https://code.visualstudio.com/docs/sourcecontrol/intro-to-git)

## Getting Help

If you encounter issues:

1. Check the [GitHub Issues](https://github.com/QueenFi703/DREDGE-Cli/issues)
2. Review the documentation files
3. Open a new issue with details about your problem

---

**Happy coding with DREDGE-Cli in VS Code! 🚀**
