.PHONY: install run test docker clean package

install:
	pip install -r requirements.txt -r requirements-dev.txt

run:
	python run.py

test:
	pytest tests/ -v

docker:
	docker compose up --build

package:
	powershell -ExecutionPolicy Bypass -File scripts/package-for-sharing.ps1

clean:
	rm -rf __pycache__ app/__pycache__ .pytest_cache instance/*.db 2>/dev/null || true

report:
	bash scripts/build-report-pdf.sh
