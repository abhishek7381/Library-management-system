import mysql.connector
import re

class LibrarySystem:
    def __init__(self, db_host, db_user, db_password, db_name):
        self.conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )
        self.cursor = self.conn.cursor()
        #self.is_admin = False
        self.create_tables()   

    def create_tables(self):
        query_books = """
        CREATE TABLE IF NOT EXISTS books (
            book_id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255),
            author VARCHAR(255),
            quantity INT
        )
        """
        query_users = """
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            email VARCHAR(255) UNIQUE,
            password VARCHAR(20) NOT NULL,
            book_id INT,
            FOREIGN KEY (book_id) REFERENCES books(book_id)
        )
        """
        query_transactions = """
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            book_id INT,
            quantity INT,
            transaction_type ENUM('Issued', 'Returned') NOT NULL,
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (book_id) REFERENCES books(book_id)
        )
        """
     
        self.cursor.execute(query_books)
        self.cursor.execute(query_users)
        self.cursor.execute(query_transactions)
        self.conn.commit()

    def add_book(self, title, author, quantity):
        query = "INSERT INTO books (title, author, quantity) VALUES (%s, %s, %s)"
        values = (title, author, quantity)
        self.cursor.execute(query, values)
        self.conn.commit()
        print("Book added successfully!")

    def is_valid_email(self, email):
        pattern = r'^\S+@\S+\.\S+$'
        return re.match(pattern, email) is not None
    
    def is_valid_password(self, password):
        if len(password) < 8:
            return False

        if not any(char.isupper() for char in password):
            return False

        if not any(char.islower() for char in password):
            return False

        if not any(char.isdigit() for char in password):
            return False

        special_characters = re.compile('[@_!#$%^&*()<>?/\|}{~:]')
        if not special_characters.search(password):
            return False
        return True
    
    def display_books(self):
        query = "SELECT * FROM books"
        self.cursor.execute(query)
        books = self.cursor.fetchall()
        if books:
            print("Books in the Library:")
            for book in books:
                print(f"ID: {book[0]}, Title: {book[1]}, Author: {book[2]}, Quantity: {book[3]}")
        else:
            print("No books available in the library.")

    def createUser(self, name, email, password):
        if self.is_valid_email(email) and self.is_valid_password(password):
            query = "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)"
            values = (name, email, password)
            self.cursor.execute(query, values)
            self.conn.commit()
            user_id = self.cursor.lastrowid
            print(f"User account created successfully!!!\nUser_ID: {user_id}")
        else:
            if not self.is_valid_email(email):
                print("Invalid email format. Please enter a valid email address.")
            if not self.is_valid_password(password):
                print("Invalid password. Password should be at least 8 characters and include at least one uppercase letter, one lowercase letter, one digit, and one special character.")

    def authenticate_user(self, email, password):
        query = "SELECT * FROM users WHERE email = %s AND password = %s"
        values = (email, password)
        self.cursor.execute(query, values)
        return self.cursor.fetchone() is not None

    def get_user_id(self, email, password):
        query = "SELECT user_id FROM users WHERE email = %s AND password = %s"
        values = (email, password)
        self.cursor.execute(query, values)
        user_id_result = self.cursor.fetchone()
        return user_id_result[0] if user_id_result else None

    def has_outstanding_books(self, email, password):
        user_id = self.get_user_id(email, password)

        if user_id is not None:
            query = "SELECT * FROM transactions WHERE user_id = %s AND transaction_type = 'Issued'"
            values = (user_id,)
            self.cursor.execute(query, values)
            return self.cursor.fetchone() is not None
        else:
            return False

    def issueBook(self, email, password, title, author):
        if self.authenticate_user(email, password):
            title = title.lower()
            author = author.lower()

            if not self.has_outstanding_books(email, password):
                query_fetch_book_id = "SELECT book_id, quantity FROM books WHERE LOWER(title) = %s AND LOWER(author) = %s AND quantity > 0"
                values_fetch_book_id = (title, author)
                self.cursor.execute(query_fetch_book_id, values_fetch_book_id)
                book_id_result = self.cursor.fetchone()

                if book_id_result:
                    book_id, quantity = book_id_result
                    query_update_books = "UPDATE books SET quantity = quantity - 1 WHERE book_id = %s"
                    values_update_books = (book_id,)
                    self.cursor.execute(query_update_books, values_update_books)

                    if self.cursor.rowcount > 0:
                        self.conn.commit()
                        user_id = self.get_user_id(email, password)
                        query_record_transaction = "INSERT INTO transactions (user_id, book_id, quantity, transaction_type) VALUES (%s, %s, %s, 'Issued')"
                        values_record_transaction = (user_id, book_id, 1)
                        self.cursor.execute(query_record_transaction, values_record_transaction)
                        self.conn.commit()
                        print("Book issued successfully!!!")
                    else:
                        print("Book is not available or quantity is insufficient!!")
                else:
                    print("Book not found. Please check the book information!!!")
            else:
                print("You have an outstanding book. Return the existing book before issuing a new one.")
        else:
            print("Invalid user credentials!!!")

    def return_book(self, email, password, title, author):
        if self.authenticate_user(email, password):
            title = title.lower()
            author = author.lower()
            query_fetch_book_id = "SELECT book_id FROM books WHERE LOWER(title) = %s AND LOWER(author) = %s"
            values_fetch_book_id = (title, author)
            self.cursor.execute(query_fetch_book_id, values_fetch_book_id)
            book_id_result = self.cursor.fetchone()

            if book_id_result:
                book_id = book_id_result[0]

                query_check_existing_issue = "SELECT * FROM transactions WHERE user_id = (SELECT user_id FROM users WHERE email = %s AND password = %s) AND book_id = %s AND transaction_type = 'Issued'"
                values_check_existing_issue = (email, password, book_id)
                self.cursor.execute(query_check_existing_issue, values_check_existing_issue)
                existing_issue = self.cursor.fetchone()

                if existing_issue:
                    query_update_books = "UPDATE books SET quantity = quantity + 1 WHERE book_id = %s"
                    values_update_books = (book_id,)
                    self.cursor.execute(query_update_books, values_update_books)

                    if self.cursor.rowcount > 0:
                        self.conn.commit()
                        query_transaction = "INSERT INTO transactions (user_id, book_id, quantity, transaction_type) VALUES ((SELECT user_id FROM users WHERE email = %s AND password = %s), %s, %s, 'Returned')"
                        values_transaction = (email, password, book_id, 1)
                        self.cursor.execute(query_transaction, values_transaction)
                        self.conn.commit()

                        print("Book returned successfully!")
                    else:
                        print("Invalid book details. Please check the book information.")
                else:
                    print("You haven't issued this book. Cannot return.")
            else:
                print("Book not found.")
        else:
            print("Invalid user credentials.")

    def display_user_details(self, email, password):
        query_user_details = "SELECT * FROM users WHERE email = %s AND password = %s"
        values_user_details = (email,password)
        self.cursor.execute(query_user_details, values_user_details)
        user = self.cursor.fetchone()

        if user:
            user_id = user[0]
            print(f"User ID: {user[0]}, Name: {user[1]}, Email: {user[2]}")
            query_transaction_history = "SELECT transactions.transaction_type, transactions.transaction_date, books.title, books.author FROM transactions JOIN books ON transactions.book_id = books.book_id WHERE transactions.user_id = %s"
            values_transaction_history = (user_id,)
            self.cursor.execute(query_transaction_history, values_transaction_history)
            transaction_history = self.cursor.fetchall()

            if transaction_history:
                print("\nBook Transaction Details:")
                for transaction in transaction_history:
                    transaction_type = transaction[0]
                    transaction_date = transaction[1]
                    book_title = transaction[2]
                    book_author = transaction[3]
                    print(f"Type: {transaction_type}, Date: {transaction_date}, Book: {book_title} by {book_author} ")
            else:
                print("No transaction history for this user.")
        else:
            print("User not found.")

    def close_connection(self):
        self.cursor.close()
        self.conn.close()

def main():
    db_host = "localhost"
    db_user = "root"
    db_password = ""
    db_name = "library_db"

    library_system = LibrarySystem(db_host, db_user, db_password, db_name)

    while True:
        print("\n SILICON LIBRARY MANAGEMENT SYSTEM")
        print("1. Add Book")
        print("2. Create User Account")
        print("3. Display Books")
        print("4. Issue Books")
        print("5. Return Book")
        print("6. User Details")
        print("7. Exit")

        choice = input("Enter your choice (1-7): ")

        if choice == "1":
            admin_ID= input("Enter admin_ID: ")
            admin_name= input("Enter admin name: ")
            pwd= input("Enter admin password: ")
            if admin_ID=="AD123" and admin_name== "jhon" and pwd=="jhon@123":
                title = input("Enter book title: ")
                author = input("Enter author: ")
                quantity = int(input("Enter quantity: "))
                library_system.add_book(title, author, quantity)
            else:
                print("You do not have permission to add books. Please log in as an admin.")
            
        elif choice=="2":
            name=input("Enter user name: ")
            email=input("Enter your email: ")
            password=input("Enter your password: ")
            library_system.createUser(name,email,password)
            
        elif choice == "3":
            library_system.display_books()

        elif choice == "4":
            email = input("Enter your email: ")
            password = input("Enter your password: ")
            title = input("Enter book name: ")
            author = input("Enter author name: ")
            library_system.issueBook(email, password, title, author)

        elif choice == "5":
            email = input("Enter your email: ")
            password = input("Enter your password: ")
            title = input("Enter book name: ")
            author = input("Enter author name: ")
            library_system.return_book(email, password, title, author)

        elif choice == "6":
            email = input("Enter your email: ")
            password = input("Enter your password: ")
            library_system.display_user_details(email,password)
            
        elif choice == "7":
            library_system.close_connection()
            print("Exiting Silicon Library.... Goodbye!")
            break

        else:
            print("Invalid choice. Please enter a number between 1 and 7.")

if __name__ == "__main__":
    main()
