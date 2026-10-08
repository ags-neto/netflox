"""Shared pytest setup for the Netflox suite.

Every test starts from a known database: the `public` schema is recreated and
schema.sql is applied (that is where the administrator required by the code comes
from), then the demo rows are loaded. The database itself is the throwaway
PostgreSQL started by `docker compose` (`make up`).
"""
from __future__ import annotations

import os
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import db as dbctl  # noqa: E402


def pytest_configure(config):
    for name in ("NETFLOX_DB_PASSWORD", "NETFLOX_DEMO_PASSWORD"):
        if not os.environ.get(name):
            raise pytest.UsageError(
                f"{name} is not set; `make test` exports both, see README (Tests)"
            )


@pytest.fixture(autouse=True)
def fresh_database():
    """Recreate the schema and reload the demo rows before every test."""
    conn = dbctl.connect()
    try:
        dbctl.apply_schema(conn)
        dbctl.seed(conn)
    finally:
        conn.close()
    yield
