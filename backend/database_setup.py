#this files sets up and initializes the SQLite database
import sqlite3
import os
#connect to database
connection = sqlite3.connect("/Users/armaanpatel/Documents/Development/net_worth/netWorthDatabase.db")
print("Database file location:", os.path.abspath("netWorthDatabase.db"))

cursor = connection.cursor()

#create tokens table
def create_tokens_tables():
    cursor.execute(""" 
    CREATE TABLE IF NOT EXISTS Tokens (
        token_id VARCHAR(225) PRIMARY KEY,
        access_token VARCHAR(225),
        request_id VARCHAR(225)
    );
    """)
    
    print("Tokens table created")

#create accounts table
def create_accounts_tables():
    cursor.execute(""" 
    CREATE TABLE IF NOT EXISTS Accounts (
        account_id VARCHAR(225) PRIMARY KEY,
        token_item_id VARCHAR(225),
        name VARCHAR(225),
        official_name VARCHAR(225),
        subtype VARCHAR(225),
        type VARCHAR(225),
        institution_id VARCHAR(225),
        request_id VARCHAR(225),
        balances REAL,
        FOREIGN KEY (token_item_id) REFERENCES Tokens(token_id) ON DELETE CASCADE
    );
    """)
    
    print("Accounts table created")

#create transactions table
def create_transactions_table():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Transactions (
        transaction_id VARCHAR(225) PRIMARY KEY,
        account_id VARCHAR(225),
        amount REAL,
        category VARCHAR(225),
        industry VARCHAR(225),
        date DATETIME,
        merchant_name VARCHAR(225),
        transaction_type VARCHAR(225),
        FOREIGN KEY (account_id) REFERENCES Accounts(account_id) ON DELETE CASCADE
    )
    """)
    print("Transactions table created")

def create_sync_table():
    cursor.execute(  
    """CREATE TABLE IF NOT EXISTS SyncState (
    access_token TEXT PRIMARY KEY,
    cursor TEXT)""")
    
    print("created")

create_tokens_tables()
create_accounts_tables()
create_transactions_table()
create_sync_table()

