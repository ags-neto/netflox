#!/usr/bin/env python3
"""Database helper for Netflox: applies schema.sql and loads the demo rows.

Used by the Makefile (`make schema`, `make seed`) and by the test suite
(tests/conftest.py), so that the schema and the seed are exercised through the
same path in both places.

Connection parameters are the ones hard-coded in database.py - localhost,
database NetfloxFinal, user postgres - and the password is read from
NETFLOX_DB_PASSWORD. The password for the seeded accounts (the administrator is
required by the code, see schema.sql) is read from NETFLOX_DEMO_PASSWORD; no
credential is stored in the repository.

    export NETFLOX_DB_PASSWORD=... NETFLOX_DEMO_PASSWORD=...
    python scripts/db.py schema   # drop + recreate the public schema, apply schema.sql
    python scripts/db.py seed     # reset the rows and insert the demo data
    python scripts/db.py reset    # schema + seed
"""
from __future__ import annotations

import os
import pathlib
import sys

import psycopg2

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA_FILE = ROOT / "schema.sql"

DB_HOST = "localhost"
DB_NAME = "NetfloxFinal"
DB_USER = "postgres"

# The demo accounts. The administrator must use an address under netflox.com,
# which is how log_in() recognises the role. Both passwords come from
# NETFLOX_DEMO_PASSWORD.
ADMIN = ("Admin", "admin@netflox.com")
DEMO_CLIENT = ("Cliente Demo", "cliente@exemplo.pt")

# (name, director, year, imdb, genre, price, type, days, [actors])
CATALOGUE = [
    ("The Matrix", "Lana Wachowski", 1999, 8.7, "sci-fi", 3.50, "movie", 7,
     ["Keanu Reeves", "Laurence Fishburne", "Carrie-Anne Moss"]),
    ("Pulp Fiction", "Quentin Tarantino", 1994, 8.9, "crime", 2.50, "movie", 7,
     ["John Travolta", "Samuel L. Jackson", "Uma Thurman"]),
    ("The Godfather", "Francis Ford Coppola", 1972, 9.2, "crime", 3.00, "movie", 7,
     ["Marlon Brando", "Al Pacino", "James Caan"]),
    ("Interstellar", "Christopher Nolan", 2014, 8.6, "sci-fi", 4.00, "movie", 14,
     ["Matthew McConaughey", "Anne Hathaway"]),
    ("Breaking Bad", "Vince Gilligan", 2008, 9.5, "drama", 5.00, "series", 30,
     ["Bryan Cranston", "Aaron Paul", "Anna Gunn"]),
    ("Stranger Things", "The Duffer Brothers", 2016, 8.7, "sci-fi", 6.00, "series", 30,
     ["Millie Bobby Brown", "Winona Ryder"]),
]


def _env(name: str, purpose: str) -> str:
    value = os.environ.get(name)
    if not value:
        sys.exit(f"{name} is not set. {purpose}")
    return value


def dsn() -> str:
    return (
        f"host={DB_HOST} dbname={DB_NAME} user={DB_USER} "
        f"password={_env('NETFLOX_DB_PASSWORD', 'Export it before touching the database.')}"
    )


def connect():
    return psycopg2.connect(dsn())


def _assert_throwaway_db(conn) -> None:
    """Refuse to drop anything that is not the throwaway database of this repo."""
    with conn.cursor() as cur:
        cur.execute("SELECT current_database()")
        name = cur.fetchone()[0]
    if name != DB_NAME:
        sys.exit(f"refusing to work on database {name!r}; expected {DB_NAME!r}")


def _close_other_sessions(conn) -> None:
    """Drop the other connections to this database before recreating the schema.

    Needed because database.py leaks connections on a few of its paths: for
    example findby_actor() raises before its conn.close() and findby_director()
    never closes on the success path. Such a session sits "idle in transaction"
    holding a lock on the tables, and DROP SCHEMA would wait for it forever.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity"
            " WHERE datname = current_database() AND pid <> pg_backend_pid()"
        )
    conn.commit()


def apply_schema(conn) -> None:
    """Recreate the public schema and apply schema.sql.

    Destructive by design: this database is disposable and the tests need a known
    starting point. The administrator password is passed to schema.sql through a
    session setting, so that it never appears in the file.
    """
    _assert_throwaway_db(conn)
    password = _env(
        "NETFLOX_DEMO_PASSWORD",
        "It is the password for the seeded accounts (schema.sql needs it).",
    )
    sql_text = SCHEMA_FILE.read_text(encoding="utf-8")
    _close_other_sessions(conn)
    with conn.cursor() as cur:
        cur.execute("DROP SCHEMA IF EXISTS public CASCADE")
        cur.execute("CREATE SCHEMA public")
        cur.execute("SET netflox.admin_password = %s", (password,))
        cur.execute(sql_text)
    conn.commit()


def seed(conn) -> None:
    """Reset the rows and insert the demo accounts and catalogue."""
    _assert_throwaway_db(conn)
    password = _env("NETFLOX_DEMO_PASSWORD", "It is the password for the seeded accounts.")
    with conn.cursor() as cur:
        cur.execute(
            "TRUNCATE users, articles, actors, articles_actors, rents, messages,"
            " pricehistory RESTART IDENTITY CASCADE"
        )
        cur.execute(
            "INSERT INTO users (nome, email, password, balance) VALUES (%s, %s, %s, 20.00)",
            (*ADMIN, password),
        )
        cur.execute(
            "INSERT INTO users (nome, email, password, balance) VALUES (%s, %s, %s, 20.00)",
            (*DEMO_CLIENT, password),
        )
        for name, director, year, rating, genre, price, kind, days, actors in CATALOGUE:
            cur.execute(
                "INSERT INTO articles (name, director, release_year, imbd_rating, genre,"
                " price, type, time_available) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                " RETURNING itemid",
                (name, director, year, rating, genre, price, kind, days),
            )
            itemid = cur.fetchone()[0]
            for actor in actors:
                cur.execute(
                    "INSERT INTO actors (name) VALUES (%s) RETURNING actorid", (actor,)
                )
                actorid = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO articles_actors (articles_itemid, actors_actorid)"
                    " VALUES (%s, %s)",
                    (itemid, actorid),
                )
    conn.commit()


def reset(conn) -> None:
    apply_schema(conn)
    seed(conn)


def main(argv: list[str]) -> int:
    action = argv[1] if len(argv) > 1 else ""
    if action not in {"schema", "seed", "reset"}:
        print(f"usage: {pathlib.Path(argv[0]).name} schema|seed|reset", file=sys.stderr)
        return 2
    conn = connect()
    try:
        if action == "schema":
            apply_schema(conn)
            print(f"schema.sql applied to {DB_NAME}")
        elif action == "seed":
            seed(conn)
            print(f"seed loaded: {len(CATALOGUE)} articles, 2 users")
        else:
            reset(conn)
            print(f"database reset: schema.sql + {len(CATALOGUE)} articles, 2 users")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
