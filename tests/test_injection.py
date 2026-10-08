"""Regression tests for the SQL injection that used to be in database.py.

Every statement in database.py was built by concatenating the value into the
SQL text, so anything that reached a search box, a sign-up form or a message
body was interpreted as SQL. Every statement is parameterized now (the value
travels as a psycopg2 parameter, never as part of the statement) and these tests
pin that.

Each test here fails against the previous, concatenating version of
database.py - see README, "Known limitations" and "Tests". The payloads are the
usual ones: a stacked `DROP TABLE`, a legitimate apostrophe, and quotes inside
the text that is stored and read back.
"""
from __future__ import annotations

import ast
import builtins
import contextlib
import os
import pathlib

import pytest

import database
from scripts import db as dbctl

ROOT = pathlib.Path(__file__).resolve().parent.parent
ADMIN_EMAIL = dbctl.ADMIN[1]

# Two statements in one call, and then a comment that swallows the trailing
# quote: `LIKE '%'; DROP TABLE users; --%'`.
DROP_PAYLOAD = "'; DROP TABLE users; --"


# --------------------------------------------------------------------------
# helpers (same shape as the ones in test_netflox.py)
# --------------------------------------------------------------------------
def demo_password() -> str:
    return os.environ["NETFLOX_DEMO_PASSWORD"]


@contextlib.contextmanager
def raw_cursor():
    """A plain connection to the throwaway database, for assertions."""
    conn = dbctl.connect()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    finally:
        conn.close()


def scalar(sql, params=None):
    with raw_cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return row[0] if row else None


def user_id(email: str) -> int:
    return scalar("SELECT userid FROM users WHERE email = %s", (email,))


def make_client(name="Ana", email="ana@exemplo.pt") -> int:
    database.create_user(name, email, demo_password())
    assert database.log_in(email, demo_password()) == 1
    return database.USERID


def feed_inputs(monkeypatch, values):
    queue = list(values)

    def fake_input(prompt=""):
        if not queue:
            raise AssertionError(f"unexpected input() call: {prompt!r}")
        return queue.pop(0)

    monkeypatch.setattr(builtins, "input", fake_input)


def insert_article(name, director, actors=(), **overrides):
    """Insert one article (and its cast) with parameterized SQL, for fixtures."""
    fields = {
        "release_year": 1995,
        "imbd_rating": 7.0,
        "genre": "drama",
        "price": 1.50,
        "type": "movie",
        "time_available": 7,
    }
    fields.update(overrides)
    with raw_cursor() as cur:
        cur.execute(
            "INSERT INTO articles (name, director, release_year, imbd_rating,"
            " genre, price, type, time_available)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING itemid",
            (name, director, fields["release_year"], fields["imbd_rating"],
             fields["genre"], fields["price"], fields["type"],
             fields["time_available"]),
        )
        itemid = cur.fetchone()[0]
        for actor in actors:
            cur.execute("INSERT INTO actors (name) VALUES (%s) RETURNING actorid",
                        (actor,))
            cur.execute(
                "INSERT INTO articles_actors (articles_itemid, actors_actorid)"
                " VALUES (%s, %s)",
                (itemid, cur.fetchone()[0]),
            )
    return itemid


# --------------------------------------------------------------------------
# (a) a stacked DROP TABLE is searched as text and changes nothing
# --------------------------------------------------------------------------
@pytest.mark.parametrize("search", [
    "findby_name", "findby_director", "findby_type", "findby_actor",
])
def test_a_drop_table_payload_is_searched_as_text(capsys, search):
    """The payload used to be pasted into the statement, which turned the search
    into two statements: the SELECT, and `DROP TABLE users`. The SELECT matching
    `LIKE '%'` also returned every article as if it were a search result.

    Now it is one parameter, the pattern matches nothing (there is no article
    with that name), and the statement is a search like any other.
    """
    result = getattr(database, search)(DROP_PAYLOAD)
    capsys.readouterr()

    # findby_actor returns None when nothing matches; the other three return [].
    assert result in ([], None)

    # The table is still there, and still has its rows, after the search.
    assert scalar("SELECT to_regclass('public.users') IS NOT NULL") is True
    assert scalar("SELECT count(*) FROM users") >= 2
    assert scalar("SELECT count(*) FROM articles") == 6


# --------------------------------------------------------------------------
# (b) a legitimate apostrophe is a character, not the end of a literal
# --------------------------------------------------------------------------
def test_an_apostrophe_in_a_search_term_is_text(capsys):
    """`LIKE '%O'Brien%'` used to be a syntax error (unterminated string)."""
    insert_article("O'Brien's Ghost", "Ana O'Brien", actors=["Sean O'Brien"])
    capsys.readouterr()

    assert [row[1] for row in database.findby_name("O'Brien")] == ["O'Brien's Ghost"]
    assert [row[1] for row in database.findby_director("O'Brien")] == ["O'Brien's Ghost"]
    assert [row[1] for row in database.findby_actor("O'Brien")] == ["O'Brien's Ghost"]
    # findby_type() searches the movie/series column, where an apostrophe can
    # only appear as a fragment that matches nothing - and it is still a
    # fragment, not the end of a string literal.
    assert database.findby_type("movie'") == []
    capsys.readouterr()


def test_an_apostrophe_in_an_admin_lookup_is_text(capsys):
    """change_price()/remove_article() look the article up by name first."""
    insert_article("O'Brien's Ghost", "Ana O'Brien")
    capsys.readouterr()

    database.change_price("O'Brien's Ghost", "2.00")
    capsys.readouterr()
    assert scalar("SELECT price FROM articles WHERE name = %s",
                  ("O'Brien's Ghost",)) == 2
    assert scalar("SELECT count(*) FROM pricehistory") == 1


# --------------------------------------------------------------------------
# (c) quotes in stored text survive a write and a read, unchanged
# --------------------------------------------------------------------------
def test_create_user_stores_quotes_exactly(capsys):
    """`VALUES ('Ana 'Aspas' Silva', ...)` used to be a syntax error."""
    name = "Ana 'Aspas' Silva"
    password = demo_password()

    database.create_user(name, "anasilva@exemplo.pt", password)
    capsys.readouterr()

    assert scalar("SELECT nome FROM users WHERE email = %s",
                  ("anasilva@exemplo.pt",)) == name
    assert scalar("SELECT password FROM users WHERE email = %s",
                  ("anasilva@exemplo.pt",)) == password
    # And the account is usable: the same quotes go through log_in().
    assert database.log_in("anasilva@exemplo.pt", password) == 1
    capsys.readouterr()


def test_a_message_with_quotes_is_stored_exactly(capsys):
    client = make_client()
    admin = user_id(ADMIN_EMAIL)
    text = "Ele disse 'olá' e \"adeus\" 'a'"
    capsys.readouterr()

    database.message_client(text, str(client), str(admin))
    capsys.readouterr()

    assert scalar("SELECT message FROM messages WHERE users_userid = %s",
                  (client,)) == text
    assert scalar("SELECT count(*) FROM messages WHERE senderid = %s",
                  (admin,)) == 1


def test_a_broadcast_with_quotes_is_stored_exactly(capsys):
    admin = user_id(ADMIN_EMAIL)
    total_users = scalar("SELECT count(*) FROM users")
    text = "Aviso: 'manutenção' \"; DROP TABLE messages; --"

    database.message_all(text, admin)
    capsys.readouterr()

    assert scalar("SELECT count(*) FROM messages WHERE message = %s",
                  (text,)) == total_users - 1
    assert scalar("SELECT count(*) FROM messages") == total_users - 1


def test_add_article_stores_quotes_exactly(monkeypatch, capsys):
    feed_inputs(monkeypatch, ["1", "Sean O'Brien"])

    database.add_article("O'Brien's Ghost", "Ana O'Brien", "7.0", "drama",
                         "1.50", "1995", "7", "movie")
    capsys.readouterr()

    itemid = scalar("SELECT itemid FROM articles WHERE name = %s",
                    ("O'Brien's Ghost",))
    assert itemid is not None
    assert scalar("SELECT director FROM articles WHERE itemid = %s",
                  (itemid,)) == "Ana O'Brien"
    assert scalar("SELECT count(*) FROM actors WHERE name = %s",
                  ("Sean O'Brien",)) == 1
    assert scalar("SELECT count(*) FROM articles_actors WHERE articles_itemid = %s",
                  (itemid,)) == 1


# --------------------------------------------------------------------------
# the password cannot be commented out or short-circuited
# --------------------------------------------------------------------------
@pytest.mark.parametrize("payload", ["' OR '1'='1", "' OR 1=1 --", "x' OR 'a'='a"])
def test_the_password_cannot_be_bypassed(capsys, payload):
    """`password = '' OR '1'='1'` used to be true for every row, so log_in()
    handed out the administrator session for any password."""
    before = database.USERID          # a failed login must not move the session
    assert database.log_in(ADMIN_EMAIL, payload) == 0
    capsys.readouterr()
    assert database.USERID == before


def test_the_email_cannot_comment_out_the_password(capsys):
    """`email = 'admin@netflox.com' --' AND password = '...'` used to match."""
    before = database.USERID
    assert database.log_in("admin@netflox.com' --", "not-the-password") == 0
    capsys.readouterr()
    assert database.USERID == before


# --------------------------------------------------------------------------
# structural guard: no statement may be assembled from parts again
# --------------------------------------------------------------------------
def test_no_statement_is_built_by_string_concatenation():
    """Every execute() must receive a constant string (plus its parameters).

    This is what the previous version looked like in all 48 interpolated
    statements: `c.execute("... = '" + value + "'")`, an ast.BinOp as the first
    argument.
    """
    source = (ROOT / "database.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        if name != "execute" or not node.args:
            continue
        statement = node.args[0]
        if not (isinstance(statement, ast.Constant) and isinstance(statement.value, str)):
            offenders.append(ast.get_source_segment(source, statement))

    assert offenders == [], f"statements assembled at runtime: {offenders}"
