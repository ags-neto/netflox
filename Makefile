# Netflox - run the app, the database, the schema and the tests.
#
# Two values come from the environment and are never written in this file:
#   NETFLOX_DB_PASSWORD    password of the throwaway PostgreSQL (compose + app)
#   NETFLOX_DEMO_PASSWORD  password for the accounts created by `make seed`
#                          and by the tests (admin@netflox.com, cliente@exemplo.pt)
#
#   export NETFLOX_DB_PASSWORD=... NETFLOX_DEMO_PASSWORD=...
#   make test

SHELL := /bin/bash
VENV  := .venv
PY    := $(VENV)/bin/python
PIP   := $(VENV)/bin/pip

export NETFLOX_DB_PASSWORD
export NETFLOX_DEMO_PASSWORD

.PHONY: help up down schema seed run test venv clean

help:
	@echo "make up      start the throwaway PostgreSQL and wait for it"
	@echo "make schema  drop and recreate the public schema, apply schema.sql"
	@echo "make seed    reset the rows and insert the demo accounts and catalogue"
	@echo "make run     run the terminal application (needs a terminal)"
	@echo "make test    run the pytest suite against the database"
	@echo "make down    stop the database and delete its volume"

$(VENV)/.deps-ok: requirements.txt requirements-dev.txt
	python3 -m venv $(VENV)
	$(PIP) install --quiet -r requirements-dev.txt
	touch $@

venv: $(VENV)/.deps-ok

up:
	@: $${NETFLOX_DB_PASSWORD:?NETFLOX_DB_PASSWORD is not set, see README}
	docker compose up -d --wait

schema: up venv
	$(PY) scripts/db.py schema

seed: schema
	$(PY) scripts/db.py seed

run: up venv
	$(PY) main.py

test: up venv
	@: $${NETFLOX_DEMO_PASSWORD:?NETFLOX_DEMO_PASSWORD is not set, see README}
	$(PY) -m pytest -q

down:
	docker compose down -v

clean:
	rm -rf $(VENV) .pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
