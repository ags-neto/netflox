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
            print("Welcome " + i[1]+"\nYour balance is:")

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

    if movies:
        for i in movies:
            break
    else:
        print("\n---movie name not correct---\n")
        return(0)

    return(x[1])
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

def create_rent(custo,email,moviename):
    conn = psycopg2.connect("host=localhost dbname=projeto user=postgres password=<REDACTED>")
    c = conn.cursor()
    timeavaible=c.execute("SELECT * FROM movies WHERE name ='"+moviename+"'")
    results = c.fetchall()
    for x in results:
        break

    userid=c.execute("SELECT * FROM users WHERE email ='"+email+"'")
    results2 = c.fetchall()
    for y in results2:
        break


    type=x[9]
    c.execute("INSERT INTO rent(clientid,date,price,dateend,usermail,timeavaible,type,movieid) VALUES ( %s, CURRENT_TIMESTAMP , %s, CURRENT_TIMESTAMP + %s * INTERVAL '1 month','"+email+"',%s,'"+type+"',%s)",(y[4],custo,x[8],x[8],x[0])) #falta  tempo aos filmes

    c.execute("SELECT date + timeavaible * INTERVAL '1 month' FROM rent;")
    results3 = c.fetchall()
    for z in results3:
        break

   # c.execute("INSERT INTO rent(dateend) VALUES('z')")

    conn.commit()
    conn.close()

def view_rent(email):
    conn = psycopg2.connect("host=localhost dbname=projeto user=postgres password=<REDACTED>")
    c = conn.cursor()
    c.execute("SELECT * FROM rent WHERE usermail = '" + email + "'")
    results = c.fetchall()
    for x in results:
        print(x)


    conn.commit()
    conn.close()


def view_avaible_movies(email):
    conn = psycopg2.connect("host=localhost dbname=projeto user=postgres password=<REDACTED>")
    c = conn.cursor()
    c.execute("SELECT * FROM rent WHERE dateend >= CURRENT_TIMESTAMP AND usermail='"+email+"'")
    results = c.fetchall()
    print("movies available:")
    id = 0
    for x in results:
        #print(x[8])
        id=x[8]
        c.execute("SELECT * FROM movies WHERE itemid =  " + str(x[8]))
        movies = c.fetchall()
        for y in movies:
            print(y[1])

    print("\n")
    print("movies not available any more:")
    c.execute("SELECT * FROM rent WHERE CURRENT_TIMESTAMP > dateend  AND usermail='" + email + "'")
    results2 = c.fetchall()
    id = 0
    for z in results2:
        id2 = z[8]
        c.execute("SELECT * FROM movies WHERE itemid =  " + str(z[8]))
        movies2 = c.fetchall()
        for r in movies2:
            print(r[1])


def findby_name(name):
    conn = psycopg2.connect("host=localhost dbname=projeto user=postgres password=<REDACTED>")
    c = conn.cursor()
    c.execute("SELECT * FROM movies WHERE name like '%" + name + "%'")
    movies = c.fetchall()
    for x in movies:
        print(x)

    if movies:
        for i in movies:
            break
    else:
        print("\n---movie name not correct---\n")
        return (0)
    print("\n")
    conn.commit()
    conn.close()

def findby_director(director):
    conn = psycopg2.connect("host=localhost dbname=projeto user=postgres password=<REDACTED>")
    c = conn.cursor()
    c.execute("SELECT * FROM movies WHERE director like '%" + director + "%'")
    movies = c.fetchall()
    for x in movies:
        print(x[3]+"----"+x[1])


    if movies:
        for i in movies:
            break
    else:
        print("\n---movie director name not correct---\n")
        return (0)
    print("\n")
    conn.commit()
    conn.close()

def findby_type(type):
    conn = psycopg2.connect("host=localhost dbname=projeto user=postgres password=<REDACTED>")
    c = conn.cursor()
    c.execute("SELECT * FROM movies WHERE type like '%" + type + "%'")
    movies = c.fetchall()
    for x in movies:
        print(x[9]+"----"+x[1])

    if movies:
        for i in movies:
            break
    else:
        print("\n---movie type not correct---\n")
        return (0)
    print("\n")
    conn.commit()
    conn.close()

def findby_actor(actor):
    conn = psycopg2.connect("host=localhost dbname=projeto user=postgres password=<REDACTED>")
    c = conn.cursor()
    c.execute("SELECT * FROM actors WHERE name like('%"+actor+"%')")
        #c.execute("SELECT * FROM actors WHERE movieid['"+str(n)+"']=5")
    actors = c.fetchall()
    for x in actors:
        break
    id=x[2]
    size=len(id)
    for y in range(0,size):
        c.execute("SELECT * FROM movies WHERE itemid=('"+str(id[y])+"')")
        movies=c.fetchall()
        for z in movies:
            print(x[1],"----",z[1])
    conn.commit()
    conn.close()


# MESSAGES
def show_unread_messages(userid):
    conn = psycopg2.connect("host=localhost dbname=projeto user=postgres password=<REDACTED>")
    c = conn.cursor()

    c.execute("SELECT * FROM messages WHERE users_userid = " + str(userid) + " AND bolread = FALSE")
    messages = c.fetchall()

    y = 0
    print("\n")
    for i in messages:
        c.execute("SELECT * FROM users WHERE userid = " + str(i[4]))
        sender = c.fetchall()
        for x in sender:
            y += 1
            print("\t" + str(y) + ") Message from " + x[1] + " date: " + str(i[5]))

    print("\t0) Exit")

    conn.commit()
    conn.close()

    return messages


def show_read_messages(userid):
    conn = psycopg2.connect("host=localhost dbname=projeto user=postgres password=<REDACTED>")
    c = conn.cursor()

    c.execute("SELECT * FROM messages WHERE users_userid = " + str(userid) + " AND bolread = TRUE")
    messages = c.fetchall()

    y = 0
    print("\n")
    for i in messages:
        c.execute("SELECT * FROM users WHERE userid = " + str(i[4]))
        sender = c.fetchall()
        for x in sender:
            y += 1
            print("\t" + str(y) + ") Message from " + x[1] + " date: " + str(i[5]))

    print("\t0) Exit")

    conn.commit()
    conn.close()

    return messages


def read_message(msgid):
    conn = psycopg2.connect("host=localhost dbname=projeto user=postgres password=<REDACTED>")
    c = conn.cursor()

    c.execute("UPDATE messages SET bolread = TRUE WHERE msgid='"+str(msgid)+"'")

    conn.commit()
    conn.close()

def view_allmovies_ordertitle():
    conn = psycopg2.connect("host=localhost dbname=projeto user=postgres password=<REDACTED>")
    c = conn.cursor()
    c.execute("SELECT * FROM movies ORDER BY name;")
    movies = c.fetchall()
    for x in movies:
        print(x[1])
    conn.commit()
    conn.close()

def view_allmovies_orderdirector():
    conn = psycopg2.connect("host=localhost dbname=projeto user=postgres password=<REDACTED>")
    c = conn.cursor()
    c.execute("SELECT * FROM movies ORDER BY director;")
    movies = c.fetchall()
    for x in movies:
        print(x[3]+"---"+x[1])
    conn.commit()
    conn.close()

def view_allmovies_orderdate():
    conn = psycopg2.connect("host=localhost dbname=projeto user=postgres password=<REDACTED>")
    c = conn.cursor()
    c.execute("SELECT * FROM movies ORDER BY year;")
    movies = c.fetchall()
    for x in movies:
        print(str(x[7])+"------"+x[1])
    conn.commit()
    conn.close()

def view_allmovies_orderimdb():
    conn = psycopg2.connect("host=localhost dbname=projeto user=postgres password=<REDACTED>")
    c = conn.cursor()
    c.execute("SELECT * FROM movies ORDER BY imdbrating;")
    movies = c.fetchall()
    for x in movies:
        print(str(x[4])+"-----"+x[1])
    conn.commit()
    conn.close()


