.PHONY: backend-install backend-run backend-test backend-lint
.PHONY: frontend-install frontend-dev frontend-build frontend-lint frontend-test frontend-format
.PHONY: docker-build docker-up docker-down ci

backend-install:
	python -m pip install -r backend/requirements.txt

backend-run:
	uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

backend-test:
	pytest backend/tests -q

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

frontend-format:
	cd frontend && npm run format

docker-build:
	docker compose build

docker-up:
	docker compose up --build

docker-down:
	docker compose down

ci: backend-lint backend-test frontend-lint frontend-test frontend-build
