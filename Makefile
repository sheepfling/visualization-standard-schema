.PHONY: install lint lint-fix typecheck test check

install:
	python3 -m pip install -e ".[dev]"

lint:
	python3 -m ruff check src tests

lint-fix:
	python3 -m ruff check --fix src tests

typecheck:
	python3 -m pyright src tests

test:
	python3 -m pytest

check: lint typecheck test
