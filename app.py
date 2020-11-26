import database

MENU = """-- Netflox --

1) Sign Up.
2) Log in.
0) Exit.

Your Selection: """


def menu():
    conn = database.conn()

    while (user_input := input(MENU)) != "0":
        print(user_input) 
        if user_input == "1":   # if
            name = input("Enter your name: ")
            email = input("Enter your e-mail: ")
            password = input("Enter your password: ")

            database.create_user(conn, name, email, password)

        elif user_input == "2":
            email = input("Enter your e-mail: ")
            password = input("Enter your password: ")
        else:
            print("Invalid input, please try again")


menu()
