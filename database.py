import os

import psycopg2
import psycopg2.errors
from contextlib import contextmanager

# Read once, at import time. Never hard-code the password here.
DB_PASSWORD = os.environ.get("NETFLOX_DB_PASSWORD")
if not DB_PASSWORD:
    raise RuntimeError(
        "NETFLOX_DB_PASSWORD is not set. Export the PostgreSQL "
        "password before running (see README.md, Configuration)."
    )

# Account of the last successful log_in(). It used to be created only by
# log_in(), so every path that ran before a login (or after leaving the menu
# with 0) failed with AttributeError; it exists from the start and is None.
USERID = None


@contextmanager
def _connection():
    """Open one connection and always close it.

    The callers keep their own commit(), which is where the data is made
    durable; this only guarantees that the session goes away on every path,
    including the early returns and the exceptions. Sessions that were left
    open stayed `idle in transaction` until something killed them.
    """
    conn = psycopg2.connect(f"host=localhost dbname=NetfloxFinal user=postgres password={DB_PASSWORD}")
    try:
        yield conn
        if not conn.closed:
            conn.commit()
    except Exception:
        if not conn.closed:
            conn.rollback()
        raise
    finally:
        if not conn.closed:
            conn.close()

# MENU
def create_user(name, email, password):
    with _connection() as conn:
        c = conn.cursor()

        if email.find('@') == -1:
            print("\n\tInsert a valid email address")

        elif email.find('netflox.com') != -1:
            print("\n\tCan't create accounts under netflox domain")

        else:
            c.execute("INSERT INTO users (nome, email, password, balance) VALUES ('" + name + "','" + email + "','" + password + "',20)")

        conn.commit()
        conn.close()
def log_in(email, password):
    with _connection() as conn:
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE email = '" + email + "' AND password = '" + password + "'")
        results = c.fetchall()

        global USERID

        conn.commit()
        conn.close()

        if email.find('netflox.com') == -1:

            if results:
                print("\n\tWelcome " + results[0][1] + ", your balance is " + str(results[0][4]) + " €")
                USERID = results[0][0]

                return 1  # client
            else:
                print("\n\tEmail and password not recognised")

                return 0

        else:
            if results:
                print("\n\tWelcome Admin " + results[0][1])
                USERID = results[0][0]
                return -1  # admin
            else:
                print("\n\tEmail and password not recognised\n")
                return 0

# MESSAGES CLIENT
def show_unread_messages(userid):
    with _connection() as conn:
        c = conn.cursor()

        c.execute("SELECT * FROM messages WHERE users_userid = " + str(userid) + " AND bolread = FALSE")
        results = c.fetchall()

        if results:
            y = 0
            print("\r")
            for i in results:
                # i[4] is the recipient, i[5] is the sender: the list used to name
                # every message after the account that received it.
                c.execute("SELECT * FROM users WHERE userid = " + str(i[5]))
                sender = c.fetchall()
                for x in sender:
                    y += 1
                    print("\t" + str(y) + ") Message from " + x[1] + " date: " + str(i[3]))

            print("\t0) Exit")
            return results

        print("\n\tNo new messages\n\t0) Exit")
        # An empty list, not None: main.py indexes what comes back, and the read
        # side has always returned a list.
        return []

def show_read_messages(userid):
    with _connection() as conn:
        c = conn.cursor()

        c.execute("SELECT * FROM messages WHERE users_userid = " + str(userid) + " AND bolread = TRUE")
        messages = c.fetchall()

        y = 0
        print("\r")
        for i in messages:
            c.execute("SELECT * FROM users WHERE userid = " + str(i[5]))
            sender = c.fetchall()
            for x in sender:
                y += 1
                print("\t" + str(y) + ") Message from " + x[1] + " date: " + str(i[3]))

        print("\t0) Exit")

        return messages

def read_message(msgid):
    with _connection() as conn:
        c = conn.cursor()

        c.execute("UPDATE messages SET bolread = TRUE WHERE msgid='" + str(msgid) + "'")

        conn.commit()
        conn.close()
# MESSAGES ADMIN
def message_all(msg, senderid):
    with _connection() as conn:
        c = conn.cursor()

        c.execute("SELECT userid FROM users")
        results = c.fetchall()

        c.execute("SELECT Sum(pg_column_size(userid))/4 as total_size FROM users")
        size = c.fetchall()[0][0]

        i = 0
        while i < size:
            if results[i][0] != senderid:
                c.execute(
                    "INSERT INTO messages (message, bolread, users_userid, senderid, data) VALUES ('" + msg + "', FALSE, '" + str(
                        results[i][0]) + "', '" + str(senderid) + "', CURRENT_DATE)")
            i += 1

        print("\n\tMessage sent to all")

        conn.commit()
        conn.close()
def message_client(msg, recieverid, senderid):
    with _connection() as conn:
        c = conn.cursor()

        c.execute(
            "INSERT INTO messages (message, bolread, users_userid, senderid, data) VALUES ('" + msg + "', FALSE, '" +
            str(recieverid) + "', '" + str(senderid) + "', CURRENT_DATE)")

        print("\n\tMessage sent successfully")

        conn.commit()
        conn.close()

# SEARCH ARTICLES
def findby_name(name):
    with _connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM articles WHERE name like '%" + name + "%'")
        movies = c.fetchall()
        y = 0
        for x in movies:
            y = y + 1
            print("\t" + str(y) + ") " + x[1])

        if not movies:
            # An empty list, not the integer 0: main.py indexes whatever comes
            # back, and 0 is not indexable.
            print("\n---movie name not correct---\n")

        return movies

def findby_director(director):
    with _connection() as conn:
        y = 0
        c = conn.cursor()
        c.execute("SELECT * FROM articles WHERE director like '%" + director + "%'")
        movies = c.fetchall()
        for x in movies:
            y = y + 1
            print("\t" + str(y) + ") " + x[1])

        if not movies:
            print("\n---movie director name not correct---\n")

        # The success path used to fall off the end of the function and return
        # None, so main.py never saw the matches it had just printed.
        return movies

def findby_type(type):
    with _connection() as conn:
        y = 0
        c = conn.cursor()
        c.execute("SELECT * FROM articles WHERE type like '%" + type + "%'")
        movies = c.fetchall()
        for x in movies:
            y = y + 1
            print("\t" + str(y) + ") " + x[1])

        if not movies:
            print("\n---movie type not correct---\n")

        # Returning before closing used to leave the session idle in
        # transaction for good; the empty case returns a list, like findby_name.
        return movies

def findby_actor(actor):
    with _connection() as conn:
        j = 0
        c = conn.cursor()
        c.execute("SELECT * FROM actors WHERE name like('%" + actor + "%')")
        actors = c.fetchall()
        print("\r")
        articles = []
        for x in actors:
            actorid = x[0]
            c.execute("SELECT * FROM articles_actors WHERE actors_actorid = '" + str(actorid) + "' ")
            articles_actors = c.fetchall()
            for y in articles_actors:
                j = j + 1
                c.execute("SELECT * FROM articles WHERE itemid  = '" + str(y[0]) + "' ")
                matched = c.fetchall()
                if matched:
                    articles.append(matched[0])
                    print(str("\t" + str(j) + ") " + matched[0][1]))

        if not articles:
            print("\n---movie actor name not correct---\n")
            # `articles` used to be an unbound name when no actor matched.
            return None

        return articles

def list_all():
    with _connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM articles")
        articles = c.fetchall()
        print('\r')

        y = 0
        for x in articles:
            y += 1
            print("\t"+str(y)+") " + x[1])
        conn.commit()
        conn.close()

        return articles
def view_details(itemid):
    with _connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM articles WHERE itemid = '"+str(itemid)+"'")
        article = c.fetchall()[0]
        print("\n\tTitle: "+str(article[1]))
        print("\tDirector: " + str(article[2]))
        print("\tYear of release: " + str(article[3]))
        print("\tIMDB rating: " + str(article[4])+"/10")
        print("\tGenre: " + str(article[5]))
        print("\tType: " + str(article[7]))
        print("\tPrice: " + str(article[6]) + "€")
        print("\tTime available: " + str(article[8]) + " days")
        print("\tActors: ")

        c.execute("SELECT * FROM articles_actors WHERE articles_itemid = '" + str(itemid) + "'")
        actors = c.fetchall()

        for i in actors:
            c.execute("SELECT * FROM actors WHERE actorid = '" + str(i[1]) + "'")
            actors_name = c.fetchall()[0][1]
            print("\t\t"+str(actors_name))

        conn.commit()
        conn.close()
def purchase(itemid, userid):
    with _connection() as conn:
        c = conn.cursor()

        c.execute("SELECT balance FROM users WHERE userid = '" + str(userid) + "'")
        balance = c.fetchall()[0][0]

        c.execute("SELECT price FROM articles WHERE itemid = '" + str(itemid) + "'")
        cost = c.fetchall()[0][0]

        if balance >= cost:
            new_balance = balance - cost
            # The debit follows the userid argument, not USERID (the account of
            # the last log_in): buying for somebody else used to charge the
            # logged-in account while the rent went to the argument.
            c.execute("UPDATE users SET balance= '" + str(new_balance) + "' WHERE userid='" + str(userid) + "'")

            c.execute("SELECT time_available FROM articles WHERE itemid = '" + str(itemid) + "'")
            time_available = c.fetchall()[0][0]

            c.execute("INSERT INTO rents (purchased_date, end_date, articles_itemid, users_userid) VALUES (CURRENT_DATE, CURRENT_DATE +" + str(int(time_available)) + ",'" + str(itemid) + "','" + str(userid) + "')")

            print("\n\tPurchase successful!")
            print("\tNew balance: " + str(new_balance) + "€")

        else:
            print("\n\tCan't afford this item")

# ORDER BY
def order_title():
    with _connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM articles ORDER BY name")
        movies = c.fetchall()
        y = 0
        print("\r")
        for x in movies:
            y += 1
            print("\t"+str(y)+") " + str(x[1]))
        print("\t0) Exit")
        conn.commit()
        conn.close()

        return movies
def order_director():
    with _connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM articles ORDER BY director")
        movies = c.fetchall()
        y = 0
        print("\r")
        for x in movies:
            y += 1
            print("\t"+str(y)+") " + str(x[2]) + " - " + str(x[1]))
        print("\t0) Exit")
        conn.commit()
        conn.close()

        return movies
def order_year():
    with _connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM articles ORDER BY release_year")
        movies = c.fetchall()
        y = 0
        print("\r")
        for x in movies:
            y += 1
            print("\t"+str(y)+") " + str(x[3]) + " - " + str(x[1]))
        print("\t0) Exit")
        conn.commit()
        conn.close()

        return movies
def order_imdb():
    with _connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM articles ORDER BY imbd_rating")
        movies = c.fetchall()
        y = 0
        print("\r")
        for x in movies:
            y += 1
            print("\t"+str(y)+") " + str(x[4]) + " - " + str(x[1]))
        print("\t0) Exit")
        conn.commit()
        conn.close()

        return movies
def order_genre():
    with _connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM articles ORDER BY genre")
        movies = c.fetchall()
        y = 0
        print("\r")
        for x in movies:
            y += 1
            print("\t"+str(y)+") " + str(x[5]) + " - " + str(x[1]))
        print("\t0) Exit")
        conn.commit()
        conn.close()

        return movies
def order_price():
    with _connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM articles ORDER BY price")
        movies = c.fetchall()
        y = 0
        print("\r")
        for x in movies:
            y += 1
            print("\t"+str(y)+") " + str(x[6]) + " - " + str(x[1]))
        print("\t0) Exit")
        conn.commit()
        conn.close()

        return movies
def order_type():
    with _connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM articles ORDER BY type")
        movies = c.fetchall()
        y = 0
        print("\r")
        for x in movies:
            y += 1
            print("\t"+str(y)+") " + str(x[7]) + " - " + str(x[1]))
        print("\t0) Exit")
        conn.commit()
        conn.close()

        return movies

# MY ARTICLES
def my_articles(userid):
    with _connection() as conn:
        c = conn.cursor()

        c.execute("SELECT * FROM rents WHERE end_date >= CURRENT_DATE AND users_userid = '" + str(userid) + "' ORDER BY articles_itemid")
        rents = c.fetchall()

        if rents:
            y = 0
            print("\n\tMy articles:\n")
            for i in rents:
                y += 1
                c.execute("SELECT * FROM articles WHERE itemid = '" + str(i[3]) + "' ORDER BY itemid")
                articles = c.fetchall()
                print("\t"+str(articles[0][0])+") "+str(articles[0][1]))

        else:
            print("\n\tYou don't have any articles")

        conn.commit()
        conn.close()

        return int(input("\t0) Exit\n\tYour selection: "))
def my_history(userid):
    with _connection() as conn:
        c = conn.cursor()

        c.execute("SELECT * FROM rents WHERE end_date < CURRENT_DATE AND users_userid = '" + str(userid) + "' ORDER BY articles_itemid")
        rents = c.fetchall()

        if rents:
            y = 0
            print("\n\tMy old articles:\n")
            for i in rents:
                y += 1
                c.execute("SELECT * FROM articles WHERE itemid = '" + str(i[3]) + "' ORDER BY itemid")
                articles = c.fetchall()
                print("\t" + str(articles[0][1]))

        else:
            print("\n\tYou don't have any old articles yet")

        conn.commit()
        conn.close()

        return int(input("\t0) Exit\n\tYour selection: "))
def time_left(itemid, userid):
    with _connection() as conn:
        c = conn.cursor()

        c.execute("SELECT * FROM rents WHERE articles_itemid = "+str(itemid)+" AND users_userid = '"+str(userid)+"'")
        time = c.fetchall()[0][2]

        print("\n\tItem available until "+str(time))

        conn.commit()
        conn.close()

# ADMIN
def add_article(name, director, imbd_rating, genre, price, year, time_available, type):
    with _connection() as conn:
        c = conn.cursor()

        c.execute("INSERT INTO articles(name, director, release_year, imbd_rating, genre, price, type, time_available)  VALUES('" + name + "','" + director + "', '" + year + "','" + imbd_rating + "','" + genre + "','" + price + "','" + type + "','" + time_available + "')")
        c.execute("SELECT * FROM articles WHERE name = '" + name + "'")
        item_id = c.fetchall()[0][0]

        n_actors = int(input("\n\tNumber of actors: "))
        x = 0
        while x < n_actors:
            x += 1
            name_actor = str(input("\n\tActor name: "))

            c.execute("SELECT * FROM actors WHERE name ='" + name_actor + "'")
            actor = c.fetchall()

            if actor:
                c.execute("INSERT INTO articles_actors(articles_itemid, actors_actorid) VALUES ('" + str(item_id) + "', '" + str(actor[0][0]) + "' )")
            else:
                c.execute("INSERT INTO actors (name) VALUES ('" + name_actor + "')")
                c.execute("SELECT * FROM actors WHERE name ='" + name_actor + "'")
                actor_id = c.fetchall()[0][0]
                c.execute("INSERT INTO articles_actors(articles_itemid, actors_actorid) VALUES ('" + str(item_id) + "', '" + str(actor_id) + "')")

        print("\n\tSuccess!")

        conn.commit()
        conn.close()
def change_price(n_id, newprice):
    with _connection() as conn:
        c = conn.cursor()

        itemid = n_id
        if isinstance(n_id, str):
            c.execute("SELECT itemid FROM articles WHERE name = '" + n_id + "'")
            n_id = c.fetchall()
            for i in n_id:
                itemid = i[0]

        c.execute("SELECT price FROM articles WHERE itemid = '" + str(itemid) + "'")
        result = c.fetchall()
        oldprice = 0
        for i in result:
            oldprice = i[0]

        c.execute("UPDATE articles SET price = '" + str(newprice) + "' WHERE itemid = '" + str(itemid) + "'")
        c.execute(
            "INSERT INTO pricehistory(old_price, change_date, articles_itemid) VALUES('" + str(oldprice) + "', CURRENT_DATE,'" + str(
                itemid) + "')")

        print("\n\tPrice updated successfully")
        print("\tOld price saved to history")

        conn.commit()
        conn.close()
def remove_article(n_id):
    with _connection() as conn:
        c = conn.cursor()

        itemid = n_id
        if isinstance(n_id, str):
            c.execute("SELECT itemid FROM articles WHERE name = '" + n_id + "'")
            n_id = c.fetchall()
            for i in n_id:
                itemid = i[0]

        c.execute("SELECT * FROM rents WHERE articles_itemid = '" + str(itemid) + "' AND CURRENT_DATE < end_date")
        result = c.fetchall()
        if result:
            print("\n\tCan't remove article because there are user(s) renting it")
            return

        # The foreign keys block the article through the rents that already ended
        # and through its price history too; checking only the open rents turned
        # the refusal into a ForeignKeyViolation traceback.
        c.execute("SELECT count(*) FROM rents WHERE articles_itemid = '" + str(itemid) + "'")
        old_rents = c.fetchall()[0][0]
        c.execute("SELECT count(*) FROM pricehistory WHERE articles_itemid = '" + str(itemid) + "'")
        price_changes = c.fetchall()[0][0]
        if old_rents or price_changes:
            kept_by = []
            if old_rents:
                kept_by.append("the rental history (" + str(old_rents) + " rent(s) that already ended)")
            if price_changes:
                kept_by.append("its price history (" + str(price_changes) + " change(s))")
            print("\n\tCan't remove article because it is kept by " + " and ".join(kept_by))
            print("\tThose records are still needed, so the article is not deleted.")
            return

        try:
            c.execute("DELETE FROM articles_actors WHERE articles_itemid = '" + str(itemid) + "'")
            c.execute("DELETE FROM articles WHERE itemid = '" + str(itemid) + "'")
        except psycopg2.errors.ForeignKeyViolation:
            conn.rollback()
            print("\n\tCan't remove article because another table still refers to it")
            print("\tNothing was deleted.")
            return

        print("\n\tArticle removed successfully")

def alter_balance(userid, balance):
    with _connection() as conn:
        c = conn.cursor()

        c.execute("UPDATE users SET balance = '" + str(balance) + "' WHERE userid='" + str(userid) + "'")

        print("\n\tBalance updated successfully")

        conn.commit()
        conn.close()
def statistics():
    with _connection() as conn:
        total=0
        c = conn.cursor()
        c.execute("SELECT articles_itemid FROM rents")
        rents = c.fetchall()
        for x in rents:
            c.execute("SELECT * FROM articles WHERE itemid= '"+str(x[0])+"' ")
            price=c.fetchall()
            for y in price:
                total=total+y[6]
        print("\rTotal spent by all users: "+str(total))

        contadorusers=0
        c.execute("SELECT * FROM users")
        users=c.fetchall()
        for y in users:
            contadorusers=contadorusers+1

        print("\rTotal number of users:  " + str(contadorusers-1))

        contadorarticles = 0
        c.execute("SELECT * FROM articles")
        articles = c.fetchall()
        for z in articles:
            contadorarticles = contadorarticles + 1
        print("\rTotal number of articles:  " + str(contadorarticles))

        contadorarticles = 0
        total_movies=0
        c.execute("SELECT * FROM articles where type = 'movie' ")
        movies = c.fetchall()
        for a in movies:
            contadorarticles = contadorarticles + 1
            total_movies=total_movies+a[6]
        print("\rTotal number of movies:  " + str(contadorarticles))

        contadorarticles = 0
        total_series=0
        c.execute("SELECT * FROM articles where type = 'series' ")
        series = c.fetchall()
        for b in series:
            contadorarticles = contadorarticles + 1
            total_series=total_series+b[6]
        print("\rTotal number of series:  " + str(contadorarticles))

        print("\rTotal spent in movies: "+str(total_movies))
        print("\rTotal spent in series: "+str(total_series))

        total2=0
        c.execute("SELECT * FROM rents WHERE end_date > CURRENT_DATE ")
        rents2 = c.fetchall()
        for e in rents2:
            c.execute("SELECT * FROM articles WHERE itemid= '"+str(e[3])+"' ")
            price2=c.fetchall()
            for d in price2:
                total2=total2+d[6]

        print("\rTotal spent on movies currently available: "+str(total2))

        conn.commit()
        conn.close()