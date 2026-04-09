.PHONY: backend-install backend-run backend-test backend-test-coverage backend-lint
.PHONY: frontend-install frontend-dev frontend-build frontend-lint frontend-test frontend-test-coverage frontend-format
.PHONY: docker-build docker-up docker-down ci ci-coverage smoke-test

backend-install:
	python -m pip install -r backend/requirements.txt

backend-run:
	uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

backend-test:
	pytest backend/tests -q

backend-test-coverage:
	pytest backend/tests -q --cov=backend/app --cov-report=term-missing --cov-report=xml --cov-fail-under=80

backend-lint:
	ruff check backend

frontend-install:
	cd frontend && npm ci

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

frontend-lint:
	cd frontend && npm run lint

frontend-test:
	cd frontend && npm run test

frontend-test-coverage:
	cd frontend && npm run test:coverage

frontend-format:
	cd frontend && npm run format

smoke-test:
	bash scripts/smoke_test.sh

docker-build:
	docker compose build

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

ci: backend-lint backend-test frontend-lint frontend-test frontend-build

ci-coverage: backend-test-coverage frontend-test-coverage
