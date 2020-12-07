import database


def menu():
    menu_interface = """-- Netflox --
    1) Sign Up
    2) Log in
    0) Exit
    Your Selection: """

    while (user_input := input(menu_interface)) != '0':

        if user_input == '1':
            print("Sign up")
            name = input("Enter your name: ")
            email = input("Enter your e-mail: ")
            password = input("Enter your password: ")
            database.create_user(name, email, password)

        elif user_input == '2':
            print("Log in")
            email = input("Enter your e-mail: ")
            password = input("Enter your password: ")
            if database.log_in(email, password):
                database.view_saldo(email)
                return(email)

        else:
            print("Invalid input, please try again")


def client():
    client_interface = """
        1) Search products
        2) View all
        3) View my products
        4) My movements
        5) Messages
        0) Exit
        Your Selection: """

    while (client_input := input(client_interface)) != '0':

        if client_input == '1':

            search_interface = """Search  by
                1) Name
                2) Actor
                3) Director
                4) Type
                0) Exit
                Your Selection: """

            while (search_input := input(search_interface)) != '0':
                if search_input == '1':
                    name = input("Insert movie name: ")
                    database.findby_name(name)
                if search_input == '2':
                    actor = input("Insert actor name: ")
                    database.findby_actor(actor)

                if search_input == '4':
                    type = input("Insert 'movie' or 'series': ")
                    database.findby_type(type)

                if search_input == '3':
                    director = input("Insert Director name: ")
                    database.findby_director(director)

                if search_input == '4':
                    type = input("Insert 'movie' or 'series': ")
                    database.findby_type(type)


        if client_input  == '2':
            database.view_allmovies()
            client_input_view = input("Select a movie or\nOrder by: 1.Title 2. Director 3.Date of release 4.Imdb rating 0.Go back\n")
            if client_input_view == '1':
                print("ordered by title:\n")
                database.view_allmovies_ordertitle()

            if client_input_view == '2':
                print("ordered by Director:\n")
                database.view_allmovies_orderdirector()
            if client_input_view == '3':
                print("ordered by Date of Realease:\n")
                database.view_allmovies_orderdate()
            if client_input_view == '4':
                print("ordered by Imdb rating:\n")
                database.view_allmovies_orderimdb()

            if (client_input_view != '0') and (client_input_view != '1') and (client_input_view != '2') and (client_input_view != '3') and (client_input_view != '4') :
                print("id  name,  actorid, director, imdbrating, genre, price, year, timeavaible, type")
                moviename=database.view_movieinfo(client_input_view)
                if moviename==0:
                     break
                client_input_view_buy =input ("press 1 to buy press 0 to leave\n")
                if client_input_view_buy == '1':
                    client_input_view_buy=input("are you sure you want to buy?\n(press 1 yes press 0 no)")
                    print("\no seu saldo é :")
                    saldo=database.view_saldo(email)
                    print(" o item custa:")
                    custo=database.view_custo(client_input_view)
                    client_input_view_buy = input("press 1 to confirm press 0 to leave\n")
                    if client_input_view_buy == '1':
                        if(custo<saldo):
                            print("item bought successefully!\n")
                            database.compra_filme(custo,saldo,email)
                            database.create_rent(custo,email,moviename)
                            print("saldo atual:\n")
                            database.view_saldo(email)
                        else:
                            print("nao tem saldo suficiente")
        if client_input == '3':
            database.view_avaible_movies(email)
            client_input_available_movies=input("Order by: 1.Title 2. Director 3.Date of release 4.Imdb rating 0.Go back\n")
            if client_input_available_movies == '1':
                print("ordered by title:\n")
                #database.view_availablemovies_ordertitle(email)
            if client_input_available_movies == '2':
                print("ordered by Director:\n")
                database.view_availablemovies_orderdirector(email)
            if client_input_available_movies == '3':
                print("ordered by Date of Realease:\n")
                #database.view_availablemovies_orderdate(email)
            if client_input_available_movies == '4':
                print("ordered by Imdb rating:\n")
                #database.view_availablemovies_orderimdb(email)


        if client_input  == '4':
            print("clientid, date start,                                   price,                     date end,                 usermail,months, id, type, movieid")
            database.view_rent(email)

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



email=menu()
#USERID=menu()

client()
