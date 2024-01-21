# Library Management System

Library Management System is a Python-based application that manages the library's book inventory, user accounts, and transactions.

## Introduction
This library management system allows users to perform various actions such as adding books, creating user accounts, displaying available books, issuing books, returning books, and viewing user details. The system uses MySQL as the database backend and includes basic authentication and authorization features.

## Features
- Add books to the library inventory.
- Create user accounts with email and password validation.
- Display available books in the library.
- Issue books to users, considering book availability and user restrictions.
- Return books to the library.
- View user details and transaction history.

## Installation
1. Install dependencies:
pip install mysql-connector-python

2. Set up the MySQL database:
Create a MySQL database named library_db.
Adjust the MySQL connection details in main() function of library_system.py (host, user, password) to match your MySQL setup.

3. Run the application:
python library_system.py
