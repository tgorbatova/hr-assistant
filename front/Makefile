.PHONY: ruff-linter
ruff-linter:
	ruff check . --fix --preview

.PHONY: ruff-formatter
ruff-formatter:
	ruff format . --preview

.PHONY: mypy
mypy:
	mypy .

lint: ruff-formatter ruff-linter mypy

.PHONY: pytest
pytest:
	pytest -v

.PHONY: coverage
coverage:
	coverage run -m pytest ./src/tests --no-summary && coverage report
