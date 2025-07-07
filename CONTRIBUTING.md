# Contributing to 389ds-log-analyser

Thank you for your interest in contributing to 389ds-log-analyser! We welcome contributions from the community and are grateful for your help in making this tool better.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)
- [Feature Requests](#feature-requests)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic understanding of LDAP and 389 Directory Server logs
- Familiarity with command-line tools

### Areas for Contribution

We welcome contributions in the following areas:

- **Bug fixes**: Help us identify and fix issues
- **New features**: Add new analysis capabilities or improve existing ones
- **Performance improvements**: Optimize parsing and analysis algorithms
- **Documentation**: Improve README, add examples, write tutorials
- **Testing**: Add test cases, improve test coverage
- **Code quality**: Refactoring, type hints, code organization

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/389ds-log-analyser.git
cd 389ds-log-analyser

# Add the upstream repository
git remote add upstream https://github.com/theoweiss/389ds-log-analyser.git
```

### 2. Create Virtual Environment

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### 3. Install Development Dependencies

```bash
# Install the package in development mode with dev dependencies
pip install -e ".[dev]"

# Verify installation
389ds-log-analyser --version
```

### 4. Verify Setup

```bash
# Run tests to ensure everything works
python -m pytest tests/ -v

# Run a quick functionality test
389ds-log-analyser src-ip-table -f test-files/access-comprehensive.log
```

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line length**: 120 characters (not 79)
- **Imports**: Group imports (standard library, third-party, local)
- **Naming**: Use descriptive names, avoid abbreviations
- **Comments**: Write clear, concise comments explaining "why", not "what"

### Type Hints

**All new code must include type hints.** This project is fully type-annotated:

```python
from typing import Optional, Dict, Any, List

def parse_log_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a single log line into a structured dictionary."""
    # Implementation here
    pass
```

### Code Organization

- **Single Responsibility**: Each function should do one thing well
- **Pure Functions**: Prefer functions without side effects when possible
- **Error Handling**: Use appropriate exception handling
- **Documentation**: Include docstrings for all public functions and classes

### Example Code Style

```python
# Good
def analyze_connections(connections: Dict[int, Connection], 
                       filter_ip: Optional[str] = None) -> List[ConnectionSummary]:
    """
    Analyze connections and return summary statistics.
    
    Args:
        connections: Dictionary of connection ID to Connection objects
        filter_ip: Optional IP address to filter connections
        
    Returns:
        List of connection summaries
        
    Raises:
        ValueError: If connections dictionary is empty
    """
    if not connections:
        raise ValueError("Connections dictionary cannot be empty")
    
    summaries: List[ConnectionSummary] = []
    for conn_id, conn in connections.items():
        if filter_ip and conn.source_ip != filter_ip:
            continue
        summaries.append(ConnectionSummary.from_connection(conn))
    
    return summaries
```

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_parser.py -v

# Run tests with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run tests in parallel (faster)
python -m pytest tests/ -n auto
```

### Writing Tests

- **Test Coverage**: Aim for high test coverage, especially for new features
- **Test Types**: Write unit tests for functions, integration tests for CLI commands
- **Test Data**: Use the existing test files in `test-files/` or create new ones
- **Assertions**: Use descriptive assertion messages

### Test Structure

```python
def test_parse_bind_operation():
    """Test parsing of BIND operation log lines."""
    # Arrange
    log_line = '[10/Jun/2025:21:18:06.100000Z] conn=100 op=0 BIND dn="uid=test,ou=people,dc=example,dc=com"'
    
    # Act
    result = parse_log_line(log_line)
    
    # Assert
    assert result is not None, "Failed to parse valid log line"
    assert result['type'] == 'BIND', f"Expected BIND, got {result['type']}"
    assert result['conn'] == 100, f"Expected conn=100, got {result['conn']}"
    assert result['dn'] == 'uid=test,ou=people,dc=example,dc=com'
```

### Test Requirements for New Features

- **Unit tests** for all new functions
- **Integration tests** for CLI commands
- **Edge case testing** (empty inputs, malformed data, etc.)
- **Performance tests** for operations on large datasets

## Pull Request Process

### Before Creating a Pull Request

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the coding standards

3. **Add tests** for your changes

4. **Run the test suite**:
   ```bash
   python -m pytest tests/ -v
   ```

5. **Update documentation** if needed

6. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add feature: brief description
   
   - Detailed description of changes
   - Any breaking changes
   - Fixes #issue_number (if applicable)"
   ```

### Pull Request Guidelines

1. **Title**: Use a clear, descriptive title
2. **Description**: Provide a detailed description of changes
3. **Link Issues**: Reference any related issues
4. **Testing**: Describe how you tested your changes
5. **Documentation**: Update documentation if needed

### Pull Request Template

```markdown
## Description
Brief description of the changes.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added tests for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows the project's coding standards
- [ ] Self-review of code completed
- [ ] Documentation updated (if needed)
- [ ] No new warnings or errors introduced
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and checks
2. **Code Review**: Maintainers review code for quality and style
3. **Testing**: Additional testing may be performed
4. **Approval**: At least one maintainer approval required
5. **Merge**: Squash and merge (typically)

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

- **Environment**: Python version, OS, tool version
- **Steps to reproduce**: Detailed steps to reproduce the issue
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **Log files**: Sample log files that demonstrate the issue (anonymized)
- **Error messages**: Full error messages and stack traces

### Issue Template

```markdown
**Bug Description**
A clear description of the bug.

**Environment**
- Python version: 
- OS: 
- Tool version: 

**Steps to Reproduce**
1. Step one
2. Step two
3. Step three

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Additional Context**
Any additional information that might help.
```

## Feature Requests

We welcome feature requests! Please:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case** clearly
3. **Explain the benefit** to users
4. **Suggest implementation** if you have ideas
5. **Consider scope** - keep features focused

## Documentation

### Types of Documentation

- **README**: User-facing documentation
- **Code comments**: Inline documentation
- **Docstrings**: Function and class documentation
- **Examples**: Usage examples and tutorials
- **API docs**: Programmatic interface documentation

### Documentation Standards

- **Clear and concise**: Use simple language
- **Examples**: Provide practical examples
- **Up-to-date**: Keep documentation current with code changes
- **Accessible**: Consider users with different experience levels

## Community

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests, questions
- **GitHub Discussions**: General discussion, ideas, help
- **Pull Requests**: Code review and collaboration

### Getting Help

- **Documentation**: Check README and code comments first
- **Search Issues**: Look for existing solutions
- **Ask Questions**: Open a GitHub issue with the "question" label
- **Community**: Engage with other contributors

### Recognition

Contributors are recognized in:
- **CHANGELOG.md**: Major contributions noted in releases
- **README.md**: Acknowledgments section
- **Git history**: All contributions are preserved in git history

## License

By contributing to this project, you agree that your contributions will be licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.

---

Thank you for contributing to 389ds-log-analyser! Your efforts help make LDAP log analysis better for everyone. 🚀
