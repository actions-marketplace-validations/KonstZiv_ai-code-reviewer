.PHONY: test lint

lint:
	flake8 src/
	black --check src/

test:
	pytest tests/ -v
