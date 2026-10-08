# Netflox

> Terminal application in Python and PostgreSQL that models a video-on-demand shop: accounts with a balance, a catalogue of films and series with their cast, rents with an end date, internal messages and a price history. Project for a Databases course unit.

## What it is

`main.py` is a menu-driven command line program; `database.py` holds every SQL statement and opens a connection per call. Signing up or logging in is decided by the address: `log_in()` treats any address under `netflox.com` as an **administrator** and every other one as a **client**.

- **Client** - search the catalogue by title, director, type or actor; list everything; order by any column; rent an item (the price is deducted from the balance and `end_date` becomes `CURRENT_DATE + time_available`); list the rentals that are still open and the expired ones; read internal messages.
- **Administrator** - add an article with its cast, change a price (the replaced price is kept in `pricehistory`), remove an article, send a message to every client or to one of them, change a balance, and print statistics.

The data model has seven tables - `users`, `articles`, `actors`, `articles_actors`, `rents`, `messages`, `pricehistory` - and it exists only in `schema.sql`: it was reconstructed from the queries, and no table or column was invented. The code reads rows by position (`SELECT *` followed by `row[1]`, `row[4]`, ...), so the column order in that file is part of the contract.

The defects the tests used to pin are fixed. `findby_director()` printed its matches and returned nothing; `findby_actor()` raised `UnboundLocalError` when no actor matched, and returned only the last article of an actor that had several; a search with no results returned the integer `0`, which `main.py` then indexed into; `purchase()` debited the account of the last login instead of the account in its argument; the message list showed the recipient's name as the author; `remove_article()` checked only the rentals that were still open, so the foreign keys on the older ones and on `pricehistory` turned the refusal into a traceback; `show_unread_messages()` returned `None` instead of an empty list; `database.USERID` was created by `log_in()`, so leaving the menu with `0` raised `AttributeError`; and several functions returned before closing their connection, leaving `idle in transaction` sessions behind. Every connection is opened and closed in one context manager now, and each of these defects has a regression test.

The archive `Projeto_Netflox_Alexandre_Almeida_Andre_Neto.zip` is not tracked any more (it was removed in commit `17f75ec`) because it contained a copy of `database.py` with the database password in clear. If that password was ever used for anything other than a local test database, it has to be rotated. The passwords used now are chosen locally and are not in the repository.

## Requirements

- Python 3.9 or newer, with `pip` (tested on 3.13).
- Docker with the Compose plugin. The application connects to `localhost:5432` and expects the database `NetfloxFinal` with the user `postgres`; `docker-compose.yml` creates exactly that, so nothing in the code has to be patched.
- Permission to talk to the Docker daemon (membership of the `docker` group is the usual way).
- Two values, taken from the environment and never stored in the repository:
  - `NETFLOX_DB_PASSWORD` - password of the throwaway PostgreSQL, used by both `docker compose` and the application;
  - `NETFLOX_DEMO_PASSWORD` - password given to the accounts that `make seed` and the tests create (`admin@netflox.com` and `cliente@exemplo.pt`).
- Runtime dependency: `psycopg2-binary` (`requirements.txt`). The tests add `pytest` (`requirements-dev.txt`).

## Install / Build

```bash
# canonical copy on the self-hosted Gitea (aneto/Netflox), mirrored to:
git clone https://github.com/ags-neto/netflox.git
cd netflox

export NETFLOX_DB_PASSWORD='<choose a password>' NETFLOX_DEMO_PASSWORD='<choose a password>'
make up      # start the throwaway PostgreSQL on 127.0.0.1:5432 and wait for it
make seed    # apply schema.sql, then load the demo accounts and catalogue
```

`make schema` and `make seed` recreate the `public` schema: they are meant for this throwaway database and discard whatever is in it. `make venv` prepares `.venv` with the dependencies; `make test` and `make run` call it as needed. `make down` stops the container and deletes its volume.

## Usage

`make run` starts the terminal program; it needs a real terminal, the database running and `NETFLOX_DB_PASSWORD` exported. This is an actual session, logged in as the demo client (`cliente@exemplo.pt`, the password is `$NETFLOX_DEMO_PASSWORD`), listing the catalogue and renting one item:

```text
    -- Netflox --
    1) Sign Up
    2) Log in
    0) Exit
    Your Selection: 2
    Log in
    Enter your e-mail: cliente@exemplo.pt
    Enter your password:
    Welcome Cliente Demo, your balance is 20.00 €

    1) Search articles
    2) List all articles
    3) Order by
    4) View my articles
    5) My history
    6) Messages
    0) Exit
    Your Selection: 2
    1) The Matrix
    2) Pulp Fiction
    3) The Godfather
    4) Interstellar
    5) Breaking Bad
    6) Stranger Things
    Your Selection: 3
    The Godfather

    1) View details
    2) Purchase
    0) Exit
    Your Selection: 2
    Are you sure (y/n): y
    Purchase successful!
    New balance: 17.00€
```

Logging in as `admin@netflox.com` gives the administrator menu instead (add article, view all, change price, remove article, messages, alter balance, statistics).

## Tests

```bash
export NETFLOX_DB_PASSWORD='...' NETFLOX_DEMO_PASSWORD='...'
make test
```

```text
.venv/bin/python -m pytest -q
........................................                                 [100%]
40 passed in 13.30s
```

The suite is end to end and needs the container: before every test `tests/conftest.py` recreates the `public` schema through the same helper the Makefile uses, and the tests then call the real functions of `database.py` - the ones `main.py` calls - against PostgreSQL. Nothing is mocked except the keyboard. It checks the column order and the keys against `information_schema`, then walks the flows: sign up and log in (including the two rejected cases), catalogue search and detail view, ordering, a rent with its balance and end date, the refused rent, current and expired rentals, a message that is read, a broadcast to everybody except the sender, adding an article with a reused actor, a price change with its history, the two removal paths, and the statistics. Three tests guard the credentials: `database.py` must refuse to import without `NETFLOX_DB_PASSWORD`, no connection string may contain a password literal, and no tracked file may contain the value of that variable.

The tests at the end of `tests/test_netflox.py` are the regression suite: each one fails against the code before the fix and passes after it - there is no `xfail` and no `test_known_bug_*` left. "Known limitations" below lists what was deliberately left alone.

### Known limitations

Not fixed, and not covered by the suite, because they are the shape of the interface
rather than a defect with a single right answer: every statement is built by string
concatenation, so the input is interpolated into the SQL; the menus index the list they
just printed without checking the range (`article[x - 1]` past the end raises
`IndexError`); and `database.my_articles()` / `database.my_history()` read from the
keyboard, which puts the menu inside the data layer.

## Structure

```text
database.py            every SQL statement and the connection; reads NETFLOX_DB_PASSWORD at import
main.py                the menus: menu() -> client() or admin()
schema.sql             the relational schema (7 tables, primary and foreign keys) and the minimal seed
scripts/db.py          applies schema.sql and loads the demo rows; used by make schema/seed and the tests
tests/conftest.py      recreates the schema before every test; tests/test_netflox.py is the suite
docker-compose.yml     throwaway PostgreSQL (NetfloxFinal, postgres, 127.0.0.1:5432)
Makefile               up, schema, seed, run, test, down (plus venv, clean, help)
requirements.txt       psycopg2-binary; requirements-dev.txt adds pytest
docs/relatorio-BD.pdf  the course report, moved from "RelatórioProjeto-BD-AndréNeto_AlexandreAlmeida_PL2.pdf"
encript.jpg            image from the original upload; no code or schema reads it and its bytes are not
                       embedded in the report (checked), so it was kept instead of deleted
```

## License

MIT — see [LICENSE](LICENSE).
