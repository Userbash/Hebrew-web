# Contributing to Hebrew AI 2025

Thank you for your interest in contributing! Here's how you can help.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/hebrew-ai-2025.git`
3. Create a feature branch: `git checkout -b feature/your-feature`
4. Make your changes
5. Test your changes
6. Push and submit a pull request

## Development Setup

```bash
# Install dependencies
cd backend && npm install
cd ../frontend && npm install

# Configure environment
cp .env.example .env

# Start development
./deploy.sh
```

## Testing

```bash
# Run all tests before submitting PR
node tests/run-all-tests.js

# Test specific component
docker-compose logs -f backend
```

## Code Standards

- Use meaningful variable names
- Add comments for complex logic
- Keep functions small and focused
- Test your changes thoroughly

## Pull Request Process

1. Ensure all tests pass: `node tests/run-all-tests.js`
2. Update README.md if needed
3. Describe changes clearly in PR description
4. Wait for review and address feedback

## Bug Reports

Include:
- Description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment (Docker version, OS, etc.)

## Feature Requests

Describe:
- The feature you'd like
- Why it's useful
- How it should work
- Any implementation ideas

## Questions?

- Open a Discussion on GitHub
- Create an Issue for bugs
- Check existing Issues/Discussions

Thank you for contributing!
