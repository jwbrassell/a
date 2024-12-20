# Contributing to AWS Manager

Thank you for your interest in contributing to the AWS Manager blueprint! This document provides guidelines and instructions for contributing.

## Code Organization

The AWS Manager blueprint follows a modular structure:

```
aws_manager/
├── models/        # Database models
├── routes/        # Route handlers
├── utils/         # Utility functions
├── static/        # Static assets
├── templates/     # HTML templates
└── tests/         # Test suite
```

## Development Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

3. Set up pre-commit hooks:
```bash
pre-commit install
```

## Coding Standards

### Python Code Style

- Follow PEP 8 guidelines
- Use type hints for function parameters and return values
- Maximum line length: 100 characters
- Use docstrings for all public modules, functions, classes, and methods

Example:
```python
from typing import List, Optional

def get_instances(region: str, filters: Optional[dict] = None) -> List[dict]:
    """
    Get EC2 instances in the specified region.

    Args:
        region: AWS region identifier
        filters: Optional filters to apply

    Returns:
        List of instance dictionaries
    
    Raises:
        ValueError: If region is invalid
    """
    pass
```

### JavaScript Code Style

- Use ES6+ features
- Maximum line length: 100 characters
- Use JSDoc comments for functions
- Use camelCase for variable and function names

Example:
```javascript
/**
 * Fetch EC2 instances for the given region.
 * @param {string} region - AWS region identifier
 * @param {Object} filters - Optional filters
 * @returns {Promise<Array>} List of instances
 */
async function getInstances(region, filters = {}) {
    // Implementation
}
```

### HTML/Template Style

- Use 2-space indentation
- Keep templates focused and modular
- Use template inheritance where appropriate
- Include proper ARIA attributes for accessibility

Example:
```html
{% extends "base.html" %}

{% block content %}
  <div class="container" role="main">
    <h1>{{ title }}</h1>
    {% include "partials/instance_list.html" %}
  </div>
{% endblock %}
```

## Testing

### Writing Tests

- Write tests for all new features
- Maintain test coverage above 90%
- Use appropriate fixtures and mocks
- Group tests logically by feature/module

Example:
```python
import pytest
from unittest.mock import patch

def test_create_instance(mock_aws_client):
    """Test EC2 instance creation"""
    with patch('boto3.client', return_value=mock_aws_client):
        result = create_instance('us-east-1', 't2.micro')
        assert result['InstanceId'] == 'i-1234567890abcdef0'
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_models.py

# Run with coverage
pytest --cov=app.blueprints.aws_manager

# Run integration tests
pytest -m integration
```

## Pull Request Process

1. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes:
- Follow coding standards
- Add/update tests
- Update documentation
- Update IMPLEMENTATION_TRACKING.md

3. Run quality checks:
```bash
# Run linter
flake8 .

# Run type checker
mypy .

# Run tests
pytest

# Run security checks
bandit -r .
```

4. Commit your changes:
```bash
git add .
git commit -m "feat: Add your feature description"
```

Follow conventional commits:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- style: Code style changes
- refactor: Code refactoring
- test: Test updates
- chore: Maintenance tasks

5. Push your changes:
```bash
git push origin feature/your-feature-name
```

6. Create a pull request:
- Use the PR template
- Link related issues
- Provide clear description
- Include test results
- Add screenshots if UI changes

## Documentation

### Code Documentation

- Use docstrings for Python code
- Use JSDoc for JavaScript code
- Keep comments focused and clear
- Update API.md for endpoint changes
- Update README.md for feature changes

### Commit Messages

Follow the conventional commits format:
```
type(scope): Description

[optional body]

[optional footer]
```

Example:
```
feat(security-groups): Add support for VPC security groups

- Add VPC security group model
- Add CRUD operations
- Add tests and documentation

Closes #123
```

## Review Process

1. Code Review Checklist:
- [ ] Follows coding standards
- [ ] Includes tests
- [ ] Updates documentation
- [ ] Passes CI checks
- [ ] No security issues
- [ ] Proper error handling
- [ ] Efficient database queries
- [ ] Clean git history

2. Testing Requirements:
- Unit tests for new code
- Integration tests for features
- Performance testing for critical paths
- Security testing for sensitive operations

3. Documentation Requirements:
- Updated API documentation
- Updated README if needed
- Clear inline documentation
- Updated IMPLEMENTATION_TRACKING.md

## Release Process

1. Version Bump:
- Update version in setup.py
- Update CHANGELOG.md
- Create version commit

2. Testing:
- Run full test suite
- Run security checks
- Test in staging environment

3. Documentation:
- Update API documentation
- Update release notes
- Update migration guides

4. Release:
- Create release tag
- Push to production
- Monitor for issues

## Getting Help

- Check existing issues
- Review documentation
- Join developer discussions
- Contact maintainers

## Code of Conduct

- Be respectful and inclusive
- Follow project guidelines
- Help others learn
- Report issues responsibly
- Maintain professional conduct

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.
