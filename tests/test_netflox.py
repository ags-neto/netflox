"""End-to-end tests for Netflox.

They run against the throwaway PostgreSQL from `docker compose`, apply schema.sql
through the same helper the Makefile uses (tests/conftest.py), and then drive the
real functions of database.py - the same ones main.py calls. Nothing is mocked
except keyboard input: if the schema does not match what the code expects, these
tests fail.

Every defect that used to be pinned here by an `xfail` or a `test_known_bug_*`
name now has a regression test that fails against the previous code; the last
section of this file is that regression suite (see README, "What it is").
"""
from __future__ import annotations

import ast
import builtins
import contextlib
import datetime
import os
import pathlib
import re
import subprocess
import sys
from decimal import Decimal

import psycopg2.errors
import pytest

import database
from scripts import db as dbctl

ROOT = pathlib.Path(__file__).resolve().parent.parent

ADMIN_EMAIL = dbctl.ADMIN[1]

# The physical column order is part of the application contract: database.py runs
# `SELECT *` and reads rows by position (row[1] is the title, row[4] the balance...).
EXPECTED_COLUMNS = {
    "users": ["userid", "nome", "email", "password", "balance"],
    "articles": ["itemid", "name", "director", "release_year", "imbd_rating",
                 "genre", "price", "type", "time_available"],
    "actors": ["actorid", "name"],
    "articles_actors": ["articles_itemid", "actors_actorid"],
    "rents": ["rentsid", "purchased_date", "end_date", "articles_itemid", "users_userid"],
    "messages": ["msgid", "message", "bolread", "data", "users_userid", "senderid"],
    "pricehistory": ["pricehistoryid", "old_price", "change_date", "articles_itemid"],
}

EXPECTED_FOREIGN_KEYS = {
    ("messages", "users_userid", "users"),
    ("messages", "senderid", "users"),
    ("rents", "articles_itemid", "articles"),
    ("rents", "users_userid", "users"),
    ("articles_actors", "articles_itemid", "articles"),
    ("articles_actors", "actors_actorid", "actors"),
    ("pricehistory", "articles_itemid", "articles"),
}


# --------------------------------------------------------------------------
# helpers
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


def rows(sql, params=None):
    with raw_cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def user_id(email: str) -> int:
    return scalar("SELECT userid FROM users WHERE email = %s", (email,))


def balance_of(userid: int) -> Decimal:
    return scalar("SELECT balance FROM users WHERE userid = %s", (userid,))


def article_id(name: str) -> int:
    return scalar("SELECT itemid FROM articles WHERE name = %s", (name,))


def today():
    return scalar("SELECT CURRENT_DATE")


def make_client(name="Ana", email="ana@exemplo.pt") -> int:
    """Register an account with the application's own code and log it in."""
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


# --------------------------------------------------------------------------
# schema
# --------------------------------------------------------------------------
def test_positional_columns_match_what_the_code_reads():
    found: dict[str, list[str]] = {}
    for table, column in rows(
        "SELECT table_name, column_name FROM information_schema.columns"
        " WHERE table_schema = 'public' ORDER BY table_name, ordinal_position"
    ):
        found.setdefault(table, []).append(column)
    assert found == EXPECTED_COLUMNS


def test_primary_and_foreign_keys():
    primary = {r[0] for r in rows(
        "SELECT table_name FROM information_schema.table_constraints"
        " WHERE constraint_type = 'PRIMARY KEY' AND table_schema = 'public'")}
    assert primary == set(EXPECTED_COLUMNS)

    foreign = {(r[0], r[1], r[2]) for r in rows(
        "SELECT tc.table_name, kcu.column_name, ccu.table_name"
        " FROM information_schema.table_constraints tc"
        " JOIN information_schema.key_column_usage kcu"
        "   ON kcu.constraint_name = tc.constraint_name"
        " JOIN information_schema.constraint_column_usage ccu"
        "   ON ccu.constraint_name = tc.constraint_name"
        " WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'"
        "   AND ccu.table_schema = 'public'")}
    assert foreign == EXPECTED_FOREIGN_KEYS


def test_userid_is_a_4_byte_integer():
    """message_all() counts recipients as Sum(pg_column_size(userid))/4."""
    assert scalar(
        "SELECT format_type(atttypid, atttypmod) FROM pg_attribute"
        " WHERE attrelid = 'users'::regclass AND attname = 'userid'") == "integer"


def test_minimal_seed_has_exactly_one_administrator():
    assert scalar("SELECT count(*) FROM users") == 2
    assert scalar("SELECT count(*) FROM users WHERE email LIKE '%@netflox.com'") == 1
    assert database.log_in(ADMIN_EMAIL, demo_password()) == -1


# --------------------------------------------------------------------------
# accounts
# --------------------------------------------------------------------------
def test_create_user_and_login(capsys):
    database.create_user("Ana Silva", "ana@exemplo.pt", "segredo")
    assert "Insert a valid email" not in capsys.readouterr().out

    assert database.log_in("ana@exemplo.pt", "segredo") == 1
    assert "Welcome Ana Silva, your balance is 20.00 €" in capsys.readouterr().out
    assert balance_of(database.USERID) == Decimal("20.00")


def test_create_user_rejects_invalid_and_netflox_addresses(capsys):
    database.create_user("Sem Arroba", "sem-arroba", "x")
    assert "Insert a valid email address" in capsys.readouterr().out

    database.create_user("Falso Admin", "root@netflox.com", "x")
    assert "Can't create accounts under netflox domain" in capsys.readouterr().out

    assert scalar("SELECT count(*) FROM users") == 2  # only the seeded rows


def test_login_rejects_a_wrong_password(capsys):
    database.create_user("Ana", "ana@exemplo.pt", "segredo")
    assert database.log_in("ana@exemplo.pt", "errado") == 0
    assert "Email and password not recognised" in capsys.readouterr().out


# --------------------------------------------------------------------------
# catalogue
# --------------------------------------------------------------------------
def test_list_all_returns_the_seeded_catalogue():
    articles = database.list_all()
    assert len(articles) == len(dbctl.CATALOGUE)
    assert {row[1] for row in articles} == {row[0] for row in dbctl.CATALOGUE}
    assert all(len(row) == len(EXPECTED_COLUMNS["articles"]) for row in articles)


def test_findby_name_matches_a_fragment_and_keeps_the_column_order():
    movies = database.findby_name("Matr")
    assert len(movies) == 1
    row = movies[0]
    assert row[1] == "The Matrix"
    assert row[2] == "Lana Wachowski"
    assert row[3] == 1999
    assert row[4] == Decimal("8.7")
    assert row[5] == "sci-fi"
    assert row[6] == Decimal("3.50")
    assert row[7] == "movie"
    assert row[8] == 7


def test_view_details_prints_every_field_and_the_cast(capsys):
    database.view_details(article_id("The Matrix"))
    out = capsys.readouterr().out
    assert "Title: The Matrix" in out
    assert "Director: Lana Wachowski" in out
    assert "Year of release: 1999" in out
    assert "IMDB rating: 8.7/10" in out
    assert "Genre: sci-fi" in out
    assert "Type: movie" in out
    assert "Price: 3.50€" in out
    assert "Time available: 7 days" in out
    assert "Keanu Reeves" in out and "Carrie-Anne Moss" in out


def test_order_by_title_and_price():
    assert [row[1] for row in database.order_title()] == sorted(
        row[0] for row in dbctl.CATALOGUE)
    prices = [row[6] for row in database.order_price()]
    assert prices == sorted(prices)


# --------------------------------------------------------------------------
# rents
# --------------------------------------------------------------------------
def test_purchase_debits_the_balance_and_creates_a_rent(capsys):
    client = make_client()
    database.purchase(article_id("The Matrix"), client)
    out = capsys.readouterr().out
    assert "Purchase successful!" in out
    assert "New balance: 16.50€" in out

    assert balance_of(client) == Decimal("16.50")
    rent = rows("SELECT purchased_date, end_date, articles_itemid, users_userid FROM rents")[0]
    assert rent[0] == today()
    assert rent[1] == today() + datetime.timedelta(days=7)
    assert rent[2] == article_id("The Matrix")
    assert rent[3] == client


def test_purchase_without_balance_changes_nothing(capsys):
    client = make_client()
    database.alter_balance(client, 1)
    database.purchase(article_id("The Matrix"), client)
    assert "Can't afford this item" in capsys.readouterr().out
    assert balance_of(client) == Decimal("1.00")
    assert scalar("SELECT count(*) FROM rents") == 0


def test_my_articles_and_time_left(monkeypatch, capsys):
    client = make_client()
    itemid = article_id("Breaking Bad")
    database.purchase(itemid, client)

    feed_inputs(monkeypatch, [str(itemid)])
    assert database.my_articles(client) == itemid
    assert "Breaking Bad" in capsys.readouterr().out

    database.time_left(itemid, client)
    assert "Item available until" in capsys.readouterr().out


def test_my_history_lists_expired_rents(monkeypatch, capsys):
    client = make_client()
    itemid = article_id("Pulp Fiction")
    database.purchase(itemid, client)
    with raw_cursor() as cur:
        cur.execute(
            "UPDATE rents SET end_date = CURRENT_DATE - 1 WHERE articles_itemid = %s",
            (itemid,),
        )

    feed_inputs(monkeypatch, ["0"])
    database.my_history(client)
    assert "Pulp Fiction" in capsys.readouterr().out

    feed_inputs(monkeypatch, ["0"])
    assert database.my_articles(client) == 0  # nothing current any more


# --------------------------------------------------------------------------
# messages
# --------------------------------------------------------------------------
def test_message_to_one_client_then_mark_it_read(capsys):
    client = make_client()
    admin = user_id(ADMIN_EMAIL)

    database.message_client("Bem-vindo", str(client), str(admin))
    assert "Message sent successfully" in capsys.readouterr().out

    unread = database.show_unread_messages(client)
    assert len(unread) == 1
    assert unread[0][1] == "Bem-vindo"                 # message text
    assert unread[0][3] == today()                     # data
    assert unread[0][4] == client                      # recipient
    assert unread[0][5] == admin                       # sender

    database.read_message(unread[0][0])
    assert scalar("SELECT bolread FROM messages") is True
    read = database.show_read_messages(client)
    assert len(read) == 1 and read[0][1] == "Bem-vindo"
    assert database.show_unread_messages(client) == []  # an empty list, not None


def test_message_all_reaches_every_user_except_the_sender(capsys):
    make_client("Ana", "ana@exemplo.pt")
    make_client("Bruno", "bruno@exemplo.pt")
    admin = user_id(ADMIN_EMAIL)
    total_users = scalar("SELECT count(*) FROM users")

    database.message_all("Aviso geral", admin)
    assert "Message sent to all" in capsys.readouterr().out

    # One message per user other than the sender, and the sender receives none.
    assert scalar("SELECT count(*) FROM messages") == total_users - 1
    assert scalar("SELECT count(DISTINCT users_userid) FROM messages") == total_users - 1
    assert scalar("SELECT count(*) FROM messages WHERE senderid = %s", (admin,)) == total_users - 1
    assert scalar("SELECT count(*) FROM messages WHERE users_userid = %s", (admin,)) == 0


# --------------------------------------------------------------------------
# admin operations
# --------------------------------------------------------------------------
def test_add_article_reuses_an_existing_actor(monkeypatch, capsys):
    feed_inputs(monkeypatch, ["2", "Keanu Reeves", "Nova Atriz"])
    database.add_article("Neo", "Lana Wachowski", "7.5", "action", "1.50",
                         "2025", "10", "movie")
    assert "Success!" in capsys.readouterr().out

    itemid = article_id("Neo")
    assert scalar("SELECT count(*) FROM articles_actors WHERE articles_itemid = %s",
                  (itemid,)) == 2
    assert scalar("SELECT count(*) FROM actors WHERE name = 'Keanu Reeves'") == 1
    assert scalar("SELECT count(*) FROM actors WHERE name = 'Nova Atriz'") == 1
    assert scalar("SELECT price FROM articles WHERE itemid = %s", (itemid,)) == Decimal("1.50")


def test_change_price_by_name_and_by_id_writes_history(capsys):
    itemid = article_id("The Matrix")
    database.change_price("The Matrix", "9.99")
    assert "Price updated successfully" in capsys.readouterr().out
    assert scalar("SELECT price FROM articles WHERE itemid = %s", (itemid,)) == Decimal("9.99")
    assert rows("SELECT old_price, change_date, articles_itemid FROM pricehistory") == [
        (Decimal("3.50"), today(), itemid)]

    database.change_price(itemid, "1.25")  # numeric id: skips the name lookup
    assert scalar("SELECT price FROM articles WHERE itemid = %s", (itemid,)) == Decimal("1.25")
    assert scalar("SELECT count(*) FROM pricehistory") == 2
    assert scalar("SELECT max(old_price) FROM pricehistory") == Decimal("9.99")


def test_remove_article_without_rentals_cleans_the_cast(capsys):
    with raw_cursor() as cur:
        cur.execute(
            "INSERT INTO articles (name, director, release_year, imbd_rating, genre,"
            " price, type, time_available) VALUES ('Temp','X',2020,5.0,'drama',1.00,"
            "'movie',5) RETURNING itemid")
        itemid = cur.fetchone()[0]
        cur.execute("INSERT INTO actors (name) VALUES ('Temp Actor') RETURNING actorid")
        cur.execute("INSERT INTO articles_actors VALUES (%s, %s)", (itemid, cur.fetchone()[0]))

    database.remove_article(str(itemid))  # main.py always passes a string
    assert "Article removed successfully" in capsys.readouterr().out
    assert scalar("SELECT count(*) FROM articles WHERE itemid = %s", (itemid,)) == 0
    assert scalar("SELECT count(*) FROM articles_actors WHERE articles_itemid = %s",
                  (itemid,)) == 0


def test_remove_article_is_refused_while_a_user_is_renting_it(capsys):
    client = make_client()
    itemid = article_id("Interstellar")
    database.purchase(itemid, client)

    database.remove_article(str(itemid))
    assert "Can't remove article" in capsys.readouterr().out
    assert scalar("SELECT count(*) FROM articles WHERE itemid = %s", (itemid,)) == 1


def test_foreign_key_blocks_deleting_an_article_with_rent_history():
    """remove_article() only checks *current* rents, but the DDL does not let the
    article disappear behind the older rents that my_history() still needs."""
    client = make_client()
    itemid = article_id("The Matrix")
    database.purchase(itemid, client)
    with raw_cursor() as cur:
        cur.execute(
            "UPDATE rents SET end_date = CURRENT_DATE - 1 WHERE articles_itemid = %s",
            (itemid,),
        )

    assert scalar("SELECT count(*) FROM rents WHERE articles_itemid = %s"
                  " AND CURRENT_DATE < end_date", (itemid,)) == 0  # code's own check passes
    with pytest.raises(psycopg2.errors.ForeignKeyViolation):
        with raw_cursor() as cur:
            cur.execute("DELETE FROM articles WHERE itemid = %s", (itemid,))


def test_alter_balance_and_statistics(capsys):
    client = make_client()
    database.alter_balance(client, 50)
    assert "Balance updated successfully" in capsys.readouterr().out
    assert balance_of(client) == Decimal("50.00")

    database.purchase(article_id("Pulp Fiction"), client)
    capsys.readouterr()
    database.statistics()
    out = capsys.readouterr().out
    assert "Total spent by all users: 2.50" in out          # rents at current prices
    # statistics() assumes exactly one administrator and prints the rest.
    assert f"Total number of users:  {scalar('SELECT count(*) FROM users') - 1}" in out
    assert "Total number of articles:  6" in out
    assert "Total number of movies:  4" in out
    assert "Total number of series:  2" in out
    assert "Total spent on movies currently available: 2.50" in out
    # "Total spent in movies" is not what the label says: it sums the whole
    # catalogue (3.50 + 2.50 + 3.00 + 4.00), not what was spent.
    assert "Total spent in movies: 13.00" in out
    assert "Total spent in series: 11.00" in out


# --------------------------------------------------------------------------
# credentials
# --------------------------------------------------------------------------
def test_database_refuses_to_start_without_the_password_env_var():
    env = {k: v for k, v in os.environ.items() if k != "NETFLOX_DB_PASSWORD"}
    proc = subprocess.run([sys.executable, "-c", "import database"],
                          cwd=ROOT, env=env, capture_output=True, text=True)
    assert proc.returncode != 0
    assert "NETFLOX_DB_PASSWORD is not set" in proc.stderr


def test_no_connection_string_carries_a_password_literal():
    source = (ROOT / "database.py").read_text(encoding="utf-8")
    connects = re.findall(r"psycopg2\.connect\((.*?)\)", source)
    assert connects, "no psycopg2.connect() found in database.py"
    assert all("password={DB_PASSWORD}" in call for call in connects)
    assert 'os.environ.get("NETFLOX_DB_PASSWORD")' in source


def test_no_tracked_file_contains_the_database_password():
    # safe.directory=* because this runs whatever user drives the container
    # (the clone can belong to somebody else, e.g. under sudo).
    proc = subprocess.run(
        ["git", "-c", "safe.directory=*", "grep", "-I", "-l", "-F",
         os.environ["NETFLOX_DB_PASSWORD"]],
        cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 1, f"the database password is committed in: {proc.stdout}"


def test_schema_sql_does_not_carry_the_demo_password():
    assert os.environ["NETFLOX_DEMO_PASSWORD"] not in (ROOT / "schema.sql").read_text(
        encoding="utf-8")


# --------------------------------------------------------------------------
# regressions: every test below used to be an xfail or a `test_known_bug_*`
# --------------------------------------------------------------------------
def test_findby_director_returns_the_rows_it_printed(capsys):
    """It printed the matches and fell off the end of the function (None)."""
    movies = database.findby_director("Christopher Nolan")
    assert movies is not None
    assert [row[1] for row in movies] == ["Interstellar"]
    assert movies[0][2] == "Christopher Nolan"        # column order kept
    assert "Interstellar" in capsys.readouterr().out

    assert database.findby_director("zzz-nao-existe") == []


def test_findby_actor_without_a_match_returns_none():
    """It used to raise UnboundLocalError: `articles` was never bound."""
    assert database.findby_actor("Ninguem Com Este Nome") is None


def test_findby_actor_returns_every_article_of_the_actor():
    """It used to return whatever `articles` held after the last iteration: only
    the last article of the actor, out of a list that could have several."""
    with raw_cursor() as cur:
        cur.execute("INSERT INTO articles (name, director, release_year, imbd_rating,"
                    " genre, price, type, time_available) VALUES ('John Wick',"
                    " 'Chad Stahelski', 2014, 7.4, 'action', 2.00, 'movie', 7)"
                    " RETURNING itemid")
        second = cur.fetchone()[0]
        cur.execute("INSERT INTO articles_actors (articles_itemid, actors_actorid)"
                    " SELECT %s, actorid FROM actors WHERE name = 'Keanu Reeves'",
                    (second,))

    movies = database.findby_actor("Keanu Reeves")
    assert sorted(row[1] for row in movies) == ["John Wick", "The Matrix"]
    assert movies[0] == database.findby_name("The Matrix")[0]


def test_search_without_matches_returns_an_empty_list():
    """It used to return the integer 0, which main.py then indexed into."""
    assert database.findby_name("zzz-nao-existe") == []
    assert database.findby_type("zzz-nao-existe") == []


def test_message_list_shows_the_sender_not_the_recipient(capsys):
    """The author was looked up with row[4] (the recipient) instead of row[5]."""
    client = make_client()
    admin = user_id(ADMIN_EMAIL)
    database.message_client("Ola", str(client), str(admin))
    capsys.readouterr()

    unread = database.show_unread_messages(client)
    out = capsys.readouterr().out
    assert "Message from Admin" in out
    assert "Message from Ana" not in out

    database.read_message(unread[0][0])               # the read list had it too
    capsys.readouterr()
    database.show_read_messages(client)
    out = capsys.readouterr().out
    assert "Message from Admin" in out
    assert "Message from Ana" not in out


def test_purchase_debits_the_account_it_was_given(capsys):
    """It debited USERID (the account of the last log_in), not its argument."""
    ana = make_client("Ana", "ana@exemplo.pt")
    bruno = make_client("Bruno", "bruno@exemplo.pt")
    assert database.log_in("ana@exemplo.pt", demo_password()) == 1  # Ana is the last login

    database.purchase(article_id("Pulp Fiction"), bruno)
    assert "Purchase successful!" in capsys.readouterr().out

    assert balance_of(bruno) == Decimal("17.50")      # 20.00 - 2.50, the buyer
    assert balance_of(ana) == Decimal("20.00")        # the last login, untouched
    assert scalar("SELECT count(*) FROM rents WHERE users_userid = %s", (bruno,)) == 1


def test_remove_article_is_refused_with_rent_history_and_it_says_why(capsys):
    """Only the *current* rents were checked, so the older ones - which the
    foreign key also protects - turned the removal into a traceback."""
    client = make_client()
    itemid = article_id("The Matrix")
    database.purchase(itemid, client)
    with raw_cursor() as cur:
        cur.execute("UPDATE rents SET end_date = CURRENT_DATE - 1"
                    " WHERE articles_itemid = %s", (itemid,))

    database.remove_article(str(itemid))              # main.py always passes a string
    out = capsys.readouterr().out
    assert "Can't remove article" in out
    assert "rental history" in out                    # explained, not a traceback
    assert scalar("SELECT count(*) FROM articles WHERE itemid = %s", (itemid,)) == 1


def test_remove_article_is_refused_while_the_price_history_keeps_it(capsys):
    """pricehistory carries a foreign key to the article as well."""
    itemid = article_id("The Matrix")
    database.change_price("The Matrix", "9.99")       # writes one pricehistory row
    capsys.readouterr()

    database.remove_article(str(itemid))
    out = capsys.readouterr().out
    assert "Can't remove article" in out
    assert "price history" in out
    assert scalar("SELECT count(*) FROM articles WHERE itemid = %s", (itemid,)) == 1
    assert scalar("SELECT count(*) FROM pricehistory") == 1


def test_a_failing_call_does_not_leave_its_session_idle_in_transaction():
    """A traceback keeps its frame alive, and the frame held the connection:
    findby_type()/findby_actor()/findby_director() returned before conn.close()
    and statistics() never closed at all, so the session stayed open."""
    try:
        database.view_details(999999)             # no such article: IndexError
    except IndexError as exc:
        held = exc.__traceback__                  # keeps the frame, and its connection
    assert held is not None

    assert scalar("SELECT count(*) FROM pg_stat_activity"
                  " WHERE datname = current_database()"
                  " AND state = 'idle in transaction'") == 0


def test_no_function_opens_a_connection_outside_the_managed_helper():
    """Structural guard: one place opens and closes, so no early return can leave
    an `idle in transaction` session behind again."""
    source = (ROOT / "database.py").read_text(encoding="utf-8")
    assert source.count("psycopg2.connect(") == 1

    tree = ast.parse(source)
    openers = sorted(
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and "psycopg2.connect(" in (ast.get_source_segment(source, node) or "")
    )
    assert openers == ["_connection"]



def test_userid_exists_and_is_none_before_any_login():
    """database.USERID was created by log_in(), so the code that runs before a
    login read an attribute that did not exist (AttributeError)."""
    proc = subprocess.run([sys.executable, "-c", "import database; print(database.USERID)"],
                          cwd=ROOT, capture_output=True, text=True, env=os.environ.copy())
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "None"


def test_leaving_the_menu_with_zero_exits_without_a_traceback():
    """`0` at the first menu used to be compared with -1, fall into the client
    branch and read database.USERID before anybody had logged in."""
    proc = subprocess.run([sys.executable, "main.py"], cwd=ROOT, input="0\n",
                          capture_output=True, text=True, env=os.environ.copy())
    assert proc.returncode == 0, proc.stderr
    assert "Traceback" not in proc.stderr
    assert "Goodbye" in proc.stdout


def test_an_administrator_login_opens_the_administrator_menu():
    proc = subprocess.run([sys.executable, "main.py"], cwd=ROOT,
                          input=f"2\n{ADMIN_EMAIL}\n{demo_password()}\n0\n",
                          capture_output=True, text=True, env=os.environ.copy())
    assert proc.returncode == 0, proc.stderr
    assert "Welcome Admin" in proc.stdout
    assert "Change price" in proc.stdout              # the administrator menu
