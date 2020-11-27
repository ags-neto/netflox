import database


def menu():

    menu_interface = """-- Netflox --
    1) Sign Up.
    2) Log in.
    0) Exit.
    Your Selection: """

    while (user_input := input(menu_interface)) != "0":
        if user_input == "1":
            print("Sign up")
            name = input("Enter your name: ")
            email = input("Enter your e-mail: ")
            password = input("Enter your password: ")
            database.create_user(name, email, password)

        elif user_input == "2":
            print("Log in")
            email = input("Enter your e-mail: ")
            password = input("Enter your password: ")
            if database.log_in(email, password):
                break

        else:
            print("Invalid input, please try again")


def client():

    client_interface = """Welcome
        1) Search products.
        2) My history.
        3) Messages.
        0) Exit
        Your Selection: """

    while (user_input := input(client_interface)) != "0":
        if user_input == "1":

            search_interface = """Order by
                    1) Name
                    2) Actor
                    3) Director
                    4) Date
                    5) 
                    6)
                    7)
                    Your Selection: """


menu()
client()
