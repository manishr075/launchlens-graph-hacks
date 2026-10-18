.PHONY: install test live-smoke run db-up up down

install:
	python -m pip install -r requirements.txt

test:
	python -m pytest -q

live-smoke:
	python scripts/live_smoke.py --reset

run:
	streamlit run app.py

db-up:
	docker compose up -d falkordb

up:
	docker compose up --build

down:
	docker compose down
