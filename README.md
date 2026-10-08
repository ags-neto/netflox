# Netflox

## Configuration

The PostgreSQL password is **not** stored in the code. `database.py`
reads it once from the environment variable `NETFLOX_DB_PASSWORD`:

```bash
export NETFLOX_DB_PASSWORD='<your-postgres-password>'
python main.py
```

If the variable is missing or empty the script stops immediately with
a `RuntimeError`; there is no default. Do not commit the value back
into the repository, and see the rotation note in the project issue
tracker if the old password was ever pushed.

**Note:** `Projeto_Netflox_Alexandre_Almeida_Andre_Neto.zip` was removed from git
tracking because it contained a copy of `database.py` with the old password.
The archive still exists on disk but must not be committed again; regenerate it
without the password if it ever needs to be published.
