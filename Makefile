.PHONY: up down build logs test

up:
	docker compose up --build -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

test:
	cd backend && .\venv\Scripts\pytest -v tests
