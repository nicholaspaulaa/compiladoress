.PHONY: test test-cov test-new

test:
	python -m pytest tests/ -v

test-cov:
	python -m pytest tests/ --cov=. --cov-report=term-missing:skip-covered --cov-fail-under=70

test-new:
	python -m pytest tests/test_app.py tests/test_auth.py tests/test_compile.py tests/test_ws_run_handler.py -v
