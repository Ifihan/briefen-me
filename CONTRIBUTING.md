# Contributing to Briefen.me

Thank you for your interest in contributing to Briefen.me! We welcome contributions from the community and appreciate your help in making this project better.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Security Vulnerabilities](#security-vulnerabilities)

## Code of Conduct

This project adheres to the Contributor Covenant [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to victoriaolusheye@gmail.com.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/briefen-me.git
   cd briefen-me
   ```
3. **Add the upstream repository**:
   ```bash
   git remote add upstream https://github.com/Ifihan/briefen-me.git
   ```
4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- Git
- A Google Gemini API key ([get one here](https://aistudio.google.com/api-keys))

### Installation

1. **Install dependencies**:

   ```bash
   uv sync
   ```

2. **Set up environment variables**:

   ```bash
   cp .env.example .env
   ```

   Edit the `.env` and add your configuration

3. **Run the application**:

   ```bash
   uv run python main.py
   ```

   The app will be available at `http://localhost:5001`

### Project Structure

```
briefen-me/
├── app/
│   ├── models/          # Database models (URL, User)
│   ├── routes/          # API and web route handlers
│   ├── services/        # Business logic (AI, scraping, validation)
│   ├── utils/           # Helper functions and decorators
│   ├── static/          # Frontend assets (CSS, JS, images)
│   └── templates/       # HTML templates
├── chrome-extension/    # Browser extension code
├── config.py           # Application configuration
└── main.py            # Application entry point
```

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

- **Bug fixes**: Help us squash bugs
- **New features**: Add new functionality
- **Documentation**: Improve or add documentation
- **Tests**: Add or improve test coverage
- **Code quality**: Refactor code, improve performance
- **UI/UX**: Enhance user interface and experience
- **Security**: Report or fix security issues

### Finding Issues to Work On

- Check the [Issues](https://github.com/Ifihan/briefen-me/issues) page
- Look for issues labeled `good first issue` for beginner-friendly tasks
- Issues labeled `help wanted` are open for anyone to work on
- Comment on an issue to let others know you're working on it

## Coding Standards

### Python Code Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions small and focused (single responsibility)
- Use type hints where appropriate

Example:

```python
def validate_url(url: str) -> tuple[bool, str, str]:
    """
    Validate and normalize a URL.

    Args:
        url: The URL to validate

    Returns:
        Tuple of (is_valid, error_message, normalized_url)
    """
    # Implementation here
```

### Frontend Code Style

- Use consistent indentation (2 spaces for HTML/CSS/JS)
- Use semantic HTML elements
- Keep CSS organized and modular
- Write clean, readable JavaScript
- Add comments for complex logic

### Security Best Practices

- **Never** expose sensitive data (API keys, passwords, etc.)
- Validate and sanitize all user input
- Use parameterized queries to prevent SQL injection
- Implement proper authentication and authorization
- Log security-relevant events server-side only
- Never expose stack traces to users (log them server-side instead)
- Properly validate URLs to prevent SSRF attacks
- Use environment variables for configuration

## Commit Guidelines

### Commit Message Format

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, missing semi-colons, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `security`: Security fixes or improvements

**Examples:**

```bash
feat(api): add endpoint for bulk URL creation

fix(scraper): handle timeout errors for slow websites

docs(readme): update installation instructions

security(api): prevent stack trace exposure in error responses
```

### Co-Authoring

When pairing or using AI assistance, add co-authors:

```
feat: implement dark mode toggle

Co-Authored-By: Partner Name <partner@example.com>
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

## Pull Request Process

### Before Submitting

1. **Test your changes thoroughly**

   - Manually test the functionality
   - Ensure existing features still work
   - Test edge cases

2. **Update documentation**

   - Update README.md if needed
   - Add/update code comments
   - Update relevant documentation

3. **Keep commits clean**
   - Use meaningful commit messages
   - Squash trivial commits if needed
   - Rebase on latest main branch

### Submitting a Pull Request

1. **Push your branch** to your fork:

   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request** on GitHub

   When you create a PR, a template will automatically be provided with sections for:
   - Description of changes
   - Type of change (bug fix, feature, etc.)
   - Related issues
   - Testing details
   - Screenshots (if applicable)
   - Checklist of requirements

   Fill out all relevant sections to help reviewers understand your changes.

3. **Respond to feedback**
   - Address review comments promptly
   - Push additional commits to your branch
   - Request re-review when ready

### Review Process

- At least one maintainer approval is required
- All CI checks must pass
- Constructive feedback is always welcome
- Be patient - reviews may take a few days

## Reporting Bugs

### Before Reporting

- Check if the bug has already been reported
- Try to reproduce the bug with the latest version
- Collect relevant information (error messages, screenshots, etc.)

### Creating a Bug Report

When you're ready to report a bug, [create a new issue](https://github.com/Ifihan/briefen-me/issues/new/choose) and select the **Bug Report** template. The template will guide you through providing all the necessary information.

## Suggesting Features

We love feature suggestions! [Create a new issue](https://github.com/Ifihan/briefen-me/issues/new/choose) and select the **Feature Request** template. The template will help you provide all the details we need to evaluate and implement your idea.

## Security Vulnerabilities

**Do not** report security vulnerabilities through public GitHub issues.

Please report security issues privately to: victoriaolusheye@gmail.com

Include:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will respond as quickly as possible and work with you to address the issue.

## Development Tips

### Running in Debug Mode

Only enable debug mode in development:

```bash
# In .env
FLASK_DEBUG=true
```

Never use debug mode in production!

### Database Migrations

When making database schema changes:

1. Update the model in `app/models/`
2. Test thoroughly
3. Document the changes

### Testing URLs Locally

Use tools like [ngrok](https://ngrok.com/) to test webhooks or external integrations:

```bash
ngrok http 5001
```

### Chrome Extension Development

The browser extension is located in `chrome-extension/`. To test:

1. Make your changes
2. Run `./build-extension.sh` to build
3. Load the extension in Chrome (Developer mode > Load unpacked)

## Questions?

If you have questions:

- Check existing [Issues](https://github.com/Ifihan/briefen-me/issues) and [Pull Requests](https://github.com/Ifihan/briefen-me/pulls)
- Create a new issue with the `question` label
- Reach out to the maintainers

## Recognition

Contributors will be recognized in:

- GitHub contributors page
- Release notes (for significant contributions)
- README acknowledgments (coming soon)

Thank you for contributing to Briefen.me! 🎉
