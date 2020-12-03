import psycopg2


def create_user(name, email, password):
    conn = psycopg2.connect("host=localhost dbname=projeto user=postgres password=<REDACTED>")
    c = conn.cursor()

    c.execute("INSERT INTO users (nome, email, password, balance) VALUES ('"+name+"','"+email+"','"+password+"',20)")

    conn.commit()
    conn.close()


def log_in(email, password):
    conn = psycopg2.connect("host=localhost dbname=projeto user=postgres password=<REDACTED>")
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE email = '"+email+"' AND password = '"+password+"'")
    results = c.fetchall()

    conn.commit()
    conn.close()

    if results:
        for i in results:
            print("Welcome " + i[1])
        return 1
    else:
        print("Email and password not recognised")
        return 0


def delete_user(userid):
    conn = psycopg2.connect("host=localhost dbname=projeto user=postgres password=<REDACTED>")
    c = conn.cursor()

    c.execute("DELETE FROM users WHERE userid = (" + userid + ")")

    conn.commit()
    conn.close()
def view_allmovies():#imprimeosfilmes
    conn = psycopg2.connect("host=localhost dbname=projeto user=postgres password=<REDACTED>")
    c = conn.cursor()
    c.execute("SELECT * FROM movies")
    movies=c.fetchall()
    for x in movies:
        print(x[1])
    conn.commit()
    conn.close()

def view_movieinfo(filme):
    conn = psycopg2.connect("host=localhost dbname=projeto user=postgres password=<REDACTED>")
    c = conn.cursor()
    c.execute("SELECT * FROM movies WHERE name = '" + filme + "'")
    movies = c.fetchall()
    for x in movies:
        print(x)
    results = c.fetchall()
    conn.commit()
    conn.close()

def view_saldo(email):
    conn = psycopg2.connect("host=localhost dbname=projeto user=postgres password=<REDACTED>")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = '" + email + "'")
    results = c.fetchall()
    for x in results:
        print(x[3])
    return(x[3])
    conn.commit()
    conn.close()

def view_custo(filme):
    conn = psycopg2.connect("host=localhost dbname=projeto user=postgres password=<REDACTED>")
    c = conn.cursor()
    c.execute("SELECT * FROM movies WHERE name = '" + filme + "'")
    results = c.fetchall()
    for x in results:
        print(x[6])
    return(x[6])
    conn.commit()
    conn.close()

def compra_filme(custo,saldo,email):
    conn = psycopg2.connect("host=localhost dbname=projeto user=postgres password=<REDACTED>")
    c = conn.cursor()
    saldofinal= saldo-custo
    c.execute("UPDATE users  SET balance=(%s) WHERE email='"+email+"'",(saldofinal,))
    conn.commit()
    conn.close()

def create_rent(custo,email):
    conn = psycopg2.connect("host=localhost dbname=projeto user=postgres password=<REDACTED>")
    c = conn.cursor()
    c.execute("INSERT INTO rent VALUES (1, 1, '2020-01-01', %s, '2020-02-01','"+email+"')",(custo,)) #falta adicionar userid e movie id whatever
    conn.commit()
    conn.close()


#proximo passo e fazer o 3 do interface
