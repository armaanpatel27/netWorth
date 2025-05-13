#file provides function to interact with database
import sqlite3
import json
from encryption import encrypt_token, decrypt_token


#cursor inside function because separate DB connection per request
def insert_tokens(db, token_id, token, request_id):
    cursor = db.cursor()

    encrypted_token = encrypt_token(token)
    cursor.execute("""
    INSERT INTO Tokens(token_id, access_token, request_id)
    VALUES (?, ?, ?)
    """, (token_id, encrypted_token, request_id))
    db.commit()
    print("Successfully inserted")

def get_tokens(db):
    cursor = db.cursor()
    cursor.execute("""
    SELECT access_token from Tokens;
    """)
    
    res = cursor.fetchall()
    array = [decrypt_token(i[0]) for i in res ]
    return array

def insert_accounts(db, account_id, token_item_id, name, official_name, subtype, type_,
    institution_id, request_id, balances):
    cursor = db.cursor()

    encrypted_token = encrypt_token(token_item_id)
    cursor.execute("""
    INSERT OR REPLACE INTO Accounts(account_id, token_item_id, name, official_name, subtype, type,
    institution_id, request_id, balances)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (account_id, encrypted_token, name, official_name, subtype, type_,
    institution_id, request_id, balances))
    db.commit()
    print("Successfully inserted")
    
def get_accounts(db):
    cursor = db.cursor()
    cursor.execute("SELECT account_id, name, balances, subtype, type, institution_id FROM Accounts")
    rows = cursor.fetchall()
    accounts = []
    for r in rows:
        accounts.append({
            "account_id": r[0],
            "name": r[1],   
            "current_balance": r[2],
            "subtype": r[3],
            "type": r[4],
            "institution_id": r[5]
        })
    return {"accounts": accounts}


    
def get_transaction_tokens(db):
    cursor = db.cursor()
    cursor.execute(""" 
    SELECT DISTINCT token_item_id 
    FROM Accounts 
    WHERE subtype = 'savings' OR subtype = 'checking' OR subtype = 'credit' """) 
    
    rows = cursor.fetchall()
    tokens = []
    for r in rows:
        tokens.append({"token" : r[0]})
    return tokens

def get_last_cursor(db, token):
    cursor = db.cursor()
    cursor.execute("SELECT cursor FROM SyncState WHERE access_token = ?", (token,))
    row = cursor.fetchone()
    return row[0] if row else None

def update_cursor(db, token, new_cursor):
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO SyncState (access_token, cursor) 
        VALUES (?, ?)
        ON CONFLICT(access_token) DO UPDATE SET cursor=excluded.cursor
    """, (token, new_cursor))
    db.commit()

def insert_transactions(db, transactions):
    cursor = db.cursor()
    for txn in transactions:
        # Extract category (ensure it's a single string and not a list or nested structure)
        category = None
        
        if isinstance(txn.get("category"), list):
            # If category is a list, take the first non-empty element as the general category
            category = txn["category"][0] if txn["category"] else None
        elif isinstance(txn.get("category"), str):
            # If category is already a string, store it directly
            category = txn["category"]
        elif isinstance(txn.get("category"), dict):
            # If category is a dictionary, extract the primary category (if available)
            category = txn["category"].get("primary", None)
        
        # Log the category being inserted for debugging
        print(f"Storing transaction with category: {category}")
        
        # Insert the transaction into the database
        cursor.execute("""
            INSERT OR IGNORE INTO Transactions (
                transaction_id, account_id, amount, category, industry,
                date, merchant_name, transaction_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            txn["transaction_id"],
            txn["account_id"],
            txn["amount"],
            category,  # Only insert the general category (no subcategories)
            txn.get("personal_finance_category", {}).get("primary", None),
            txn["date"],
            txn.get("merchant_name"),
            txn["transaction_type"]
        ))

    db.commit()






