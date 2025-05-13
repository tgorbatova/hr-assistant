.PHONY: ruff-linter
ruff-linter:
	uv run ruff check . --fix --preview

.PHONY: ruff-formatter
ruff-formatter:
	uv run ruff format . --preview

.PHONY: mypy
mypy:
	uv run mypy . --strict --no-warn-unused-ignores

.PHONY: pyright
pyright:
	uv run pyright .

lint: ruff-formatter ruff-linter mypy pyright

.PHONY: coverage
coverage:
	coverage run -m pytest ./src/tests --no-summary && coverage report
