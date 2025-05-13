import sqlite3 
import os

connection = sqlite3.connect("/Users/armaanpatel/Documents/Development/net_worth/netWorthDatabase.db")
print("Database file location:", os.path.abspath("netWorthDatabase.db"))


cursor = connection.cursor()

cursor.execute("""
DROP TABLE Accounts
""")

cursor.execute("""
DROP TABLE Tokens
            """)

cursor.execute("""
DROP TABLE Transactions
            """)