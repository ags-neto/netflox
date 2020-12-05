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
                break

        else:
            print("Invalid input, please try again")
    return(email)

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
                4) Date
                5) IMDB rating
                6) Genre
                7) Price
                0) Exit
                Your Selection: """

            # range of dates
            # range of prices

            while (search_input := input(search_interface)) != '0':

                if search_input == '1':
                    name = input("Insert actor name: ")
                    database.findby_name(name)  # doesnt exist yet
        if client_input  == '2':
            database.view_allmovies()
            client_interface_view = "\nselecione um filme ou pressione zero para saír "
            while (client_input_view := input(client_interface_view)) !='0':
                if client_input_view != '0':
                    moviename=database.view_movieinfo(client_input_view)
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






email=menu()

client()
