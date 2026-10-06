# Contributing to searxng-instance-mcp

Thank you for your interest in contributing!

## Development Setup

```bash
# Clone the repository
git clone https://github.com/hemeligur/searxng-instance-mcp.git
cd searxng-instance-mcp

# Install dependencies
uv sync

# Install dev dependencies
uv sync --extra dev
```

## Code Quality

We use ruff and pyright for code quality:

```bash
# Lint
uv run ruff check src/

# Type check
uv run pyright src/
```

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/searxng_mcp --cov-report=term-missing
```

## Commit Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat(search): add timeout parameter
fix(circuit-breaker): prevent false positives on 429
docs(readme): add installation section
test(discovery): add test for TLS filtering
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Make your changes
4. Run tests and ensure they pass
5. Commit using conventional commits
6. Push and open a PR

## Reporting Issues

- Use GitHub Issues for bugs and feature requests
- For security issues, see [SECURITY.md](SECURITY.md)

## License

By contributing, you agree that your contributions will be licensed under the GNU General Public License v3.0.
