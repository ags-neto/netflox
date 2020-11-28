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
                break

        else:
            print("Invalid input, please try again")


def client():
    client_interface = """
        1) Search products
        2) View all
        2) My history
        3) Messages
        0) Exit
        Your Selection: """

    while (client_input := input(client_interface)) != '0':

        if client_input == '1':

            search_interface = """Order by
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
                    database.view_movieinfo(client_input_view)





menu()
client()