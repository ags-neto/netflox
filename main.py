import database


def menu():
    menu_interface = """
    -- Netflox --
    1) Sign Up
    2) Log in
    0) Exit
    Your Selection: """

    while (user_input := input(menu_interface)) != '0':

        if user_input == '1':
            print("\n\tSign up")
            name = input("\tEnter your name: ")
            email = input("\tEnter your e-mail: ")
            password = input("\tEnter your password: ")
            database.create_user(name, email, password)

        elif user_input == '2':
            print("\n\tLog in")
            email = input("\tEnter your e-mail: ")
            password = input("\tEnter your password: ")
            user = database.log_in(email, password)
            if user == -1:
                return user  # admin
            elif user == 1:
                return user  # client

        else:
            print("Invalid input, please try again")
def client():
    order_interface = """
    1) Title
    2) Director
    3) Release Year
    4) IMDB Rating
    5) Genre
    6) Price
    7) Type
    0) Exit
    Your Selection: """
    article_interface = """
    1) View details
    2) Purchase
    0) Exit
    Your Selection: """
    client_interface = """
    1) List all articles
    2) Order by
    3) View my articles
    4) My history
    5) Messages
    0) Exit
    Your Selection: """
    while (client_input := input(client_interface)) != '0':
        if client_input == '1':
            article = database.list_all()
            while (x := int(input("\tYour Selection: "))) != 0:
                print("\n\t" + article[x - 1][1])
                while (client_in := input(article_interface)) != '0':
                    if client_in == '1':
                        database.view_details(article[x - 1][0])
                    if client_in == '2':
                        if str(input("\n\tAre you sure (y/n): ")) == "y":
                            database.purchase(article[x - 1][0], USERID)
                            pass
                        else:
                            pass
                break

        if client_input == '2':
            while (client_in := input(order_interface)) != '0':
                if client_in == '1':
                    article = database.order_title()
                    while (x := int(input("\tYour Selection: "))) != 0:
                        print("\n\t" + article[x - 1][1])
                        while (client_in := input(article_interface)) != '0':
                            if client_in == '1':
                                database.view_details(article[x - 1][0])
                            if client_in == '2':
                                if str(input("\n\tAre you sure (y/n): ")) == "y":
                                    database.purchase(article[x - 1][0], USERID)
                                    break
                                else:
                                    pass
                        break
                    break
                if client_in == '2':
                    article = database.order_director()
                    while (x := int(input("\tYour Selection: "))) != 0:
                        print("\n\t" + article[x - 1][1])
                        while (client_in := input(article_interface)) != '0':
                            if client_in == '1':
                                database.view_details(article[x - 1][0])
                            if client_in == '2':
                                if str(input("\n\tAre you sure (y/n): ")) == "y":
                                    database.purchase(article[x - 1][0], USERID)
                                    break
                                else:
                                    pass
                        break
                    break
                if client_in == '3':
                    article = database.order_year()
                    while (x := int(input("\tYour Selection: "))) != 0:
                        print("\n\t" + article[x - 1][1])
                        while (client_in := input(article_interface)) != '0':
                            if client_in == '1':
                                database.view_details(article[x-1][0])
                            if client_in == '2':
                                if str(input("\n\tAre you sure (y/n): ")) == "y":
                                    database.purchase(article[x-1][0], USERID)
                                    break
                                else:
                                    pass
                        break
                    break
                if client_in == '4':
                    article = database.order_imdb()
                    while (x := int(input("\tYour Selection: "))) != 0:
                        print("\n\t" + article[x - 1][1])
                        while (client_in := input(article_interface)) != '0':
                            if client_in == '1':
                                database.view_details(article[x - 1][0])
                            if client_in == '2':
                                if str(input("\n\tAre you sure (y/n): ")) == "y":
                                    database.purchase(article[x - 1][0], USERID)
                                    break
                                else:
                                    pass
                        break
                    break
                if client_in == '5':
                    article = database.order_genre()
                    while (x := int(input("\tYour Selection: "))) != 0:
                        print("\n\t" + article[x - 1][1])
                        while (client_in := input(article_interface)) != '0':
                            if client_in == '1':
                                database.view_details(article[x - 1][0])
                            if client_in == '2':
                                if str(input("\n\tAre you sure (y/n): ")) == "y":
                                    database.purchase(article[x - 1][0], USERID)
                                    break
                                else:
                                    pass
                        break
                    break
                if client_in == '6':
                    article = database.order_price()
                    while (x := int(input("\tYour Selection: "))) != 0:
                        print("\n\t" + article[x - 1][1])
                        while (client_in := input(article_interface)) != '0':
                            if client_in == '1':
                                database.view_details(article[x - 1][0])
                            if client_in == '2':
                                if str(input("\n\tAre you sure (y/n): ")) == "y":
                                    database.purchase(article[x - 1][0], USERID)
                                    break
                                else:
                                    pass
                        break
                    break
                if client_in == '7':
                    article = database.order_type()
                    while (x := int(input("\tYour Selection: "))) != 0:
                        print("\n\t" + article[x - 1][1])
                        while (client_in := input(article_interface)) != '0':
                            if client_in == '1':
                                database.view_details(article[x - 1][0])
                            if client_in == '2':
                                if str(input("\n\tAre you sure (y/n): ")) == "y":
                                    database.purchase(article[x - 1][0], USERID)
                                    break
                                else:
                                    pass
                        break
                    break

        if client_input == '3':
            article_id = database.my_articles(USERID)
            if article_id != 0:
                database.time_left(article_id, USERID)

        if client_input == '4':
            if database.my_history(USERID) == 0:
                pass

        if client_input == '5':
            message_interface = """
    1) View unread messages
    2) View read messages
    0) Exit
    Your Selection: """
            while (client_input := input(message_interface)) != '0':
                if client_input == '1':
                    y = database.show_unread_messages(USERID)
                    while (x := int(input("\tYour Selection: "))) != 0:
                        database.read_message(y[x - 1][0])
                        print("\n\t" + y[x - 1][1])
                        print("\n\t0) Go back")

                if client_input == '2':
                    y = database.show_read_messages(USERID)
                    while (x := int(input("\tYour Selection: "))) != 0:
                        print("\n\t" + y[x - 1][1])
                        print("\n\t0) Go back")
def admin():
    admin_interface = """
    1) Add new article
    2) View all
    3) Change price
    4) Remove article
    5) Messages
    6) Alter user balance
    0) Exit
    Your Selection: """
    admin_article = """
    1) View details
    0) Exit
    Your Selection: """
    while (admin_input := input(admin_interface)) != '0':

        if admin_input == '1':
            print("\n\tAdd new article")
            name = str(input("\tName: "))
            director = str(input("\tDirector: "))
            imbdrating = str(input("\tIMDB rating: "))
            genre = str(input("\tGenre: "))
            price = str(input("\tPrice: "))
            year = str(input("\tYear of release: "))
            days_available = str(input("\tDays available: "))
            type = str(input("\tType: "))
            database.add_article(name, director, imbdrating, genre, price, year, days_available, type)

        if admin_input == '2':
            article = database.list_all()
            while (x := int(input("\tYour Selection: "))) != 0:
                print("\n\t" + article[x - 1][1])
                while (admin_in := input(admin_article)) != '0':
                    if admin_in == '1':
                        database.view_details(article[x - 1][0])
                    else:
                        break
                break

        if admin_input == '3':
            print("\n\tChange price")
            n_id = input("\tMovie name or id: ")
            new_price = input("\tNew Price: ")
            database.change_price(n_id, new_price)

        if admin_input == '4':
            print("\n\tRemove article")
            n_id = input("\tMovie name or id: ")
            database.remove_article(n_id)

        if admin_input == '5':
            message_interface = """
    1) Send message to all
    2) Send message to a client
    0) Exit
    Your Selection: """
            while (admin_input := input(message_interface)) != '0':
                if admin_input == '1':
                    print("\n\tSend message to all")
                    msg = input("\tMessage: ")
                    database.message_all(msg, database.USERID)

                if admin_input == '2':
                    print("\n\tSend message to a client")
                    msg = input("\tMessage: ")
                    recieverid = input("\tClient id: ")
                    database.message_client(msg, recieverid, database.USERID)

        if admin_input == '6':
            print("\n\tAlter user balance")
            userid = input("\tUser id: ")
            balance = input("\tNew balance: ")
            database.alter_balance(userid, balance)


if menu() != -1:
    USERID = database.USERID
    client()
else:
    USERID = database.USERID
    admin()
