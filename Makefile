.PHONY: install test lint

install:
	python3 -m pip install -e ".[dev]"

test:
	pytest -q

lint:
	python3 -m compileall -q src tests
