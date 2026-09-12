.PHONY: test unit-test integration-test lint

test:
	pytest backend/tests/ -v

unit-test:
	pytest backend/tests/unit/ -v

integration-test:
	pytest backend/tests/integration/ -v
