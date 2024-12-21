# AWS Manager Blueprint Makefile

.PHONY: help test coverage lint format clean install dev-install

help:
	@echo "Available commands:"
	@echo "  make install      - Install production dependencies"
	@echo "  make dev-install  - Install development dependencies"
	@echo "  make test        - Run tests"
	@echo "  make coverage    - Run tests with coverage report"
	@echo "  make lint        - Run linting checks"
	@echo "  make format      - Format code"
	@echo "  make clean       - Clean up build artifacts"

install:
	pip install -r requirements.txt

dev-install:
	pip install -r tests/requirements.txt

test:
	pytest tests/test_aws_manager.py -v

coverage:
	pytest tests/test_aws_manager.py --cov=. --cov-report=html --cov-report=term

lint:
	flake8 .
	mypy .
	black . --check
	isort . --check-only

format:
	black .
	isort .

clean:
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf tests/htmlcov
	rm -rf __pycache__
	rm -rf tests/__pycache__
	rm -rf .mypy_cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info

# Development shortcuts
.PHONY: run-tests watch-tests

run-tests:
	pytest tests/test_aws_manager.py -v --tb=short

watch-tests:
	ptw tests/test_aws_manager.py -- -v --tb=short

# Docker support
.PHONY: docker-build docker-test

docker-build:
	docker build -t aws-manager-tests -f tests/Dockerfile .

docker-test:
	docker run --rm aws-manager-tests pytest tests/test_aws_manager.py -v

# Documentation
.PHONY: docs serve-docs

docs:
	cd docs && make html

serve-docs:
	cd docs/_build/html && python -m http.server 8000

# Database
.PHONY: db-init db-migrate db-upgrade

db-init:
	flask db init

db-migrate:
	flask db migrate -m "AWS Manager migration"

db-upgrade:
	flask db upgrade

# Vault operations
.PHONY: vault-init vault-unseal

vault-init:
	python -m scripts.vault_init

vault-unseal:
	python -m scripts.vault_unseal

# AWS operations
.PHONY: aws-configure aws-test-connection

aws-configure:
	python -m scripts.aws_configure

aws-test-connection:
	python -m scripts.aws_test_connection

# Quality checks
.PHONY: security-check type-check

security-check:
	bandit -r .
	safety check

type-check:
	mypy .
	pytype .

# CI tasks
.PHONY: ci-test ci-lint ci-security

ci-test: install dev-install test coverage

ci-lint: dev-install lint

ci-security: dev-install security-check

# Release tasks
.PHONY: build publish

build: clean
	python setup.py sdist bdist_wheel

publish: build
	twine upload dist/*

# Environment setup
.PHONY: setup-dev setup-prod

setup-dev: dev-install
	pre-commit install
	pip install -e .

setup-prod: install
	pip install -e .

# Default target
.DEFAULT_GOAL := help
