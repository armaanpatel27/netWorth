from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from dotenv import load_dotenv
from plaid.configuration  import Configuration
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from database import insert_tokens, get_tokens, insert_accounts, get_accounts, get_transaction_tokens, get_last_cursor, update_cursor, insert_transactions
import sqlite3 
from encryption import encrypt_token, decrypt_token
import datetime
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.transactions_sync_response import TransactionsSyncResponse

import os



load_dotenv()

#initalizes a FastAPI application
app = FastAPI()

#middleware to allow frontend to make calls to this file
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#create a Plaid configuration --> interface to make API calls
configuration = Configuration(
    host= "https://production.plaid.com",
    api_key={
        'clientId': os.getenv("PLAID_CLIENT_ID"),
        'secret': os.getenv("PLAID_SANDBOX"),
    }
)

#client is interface 
api_client = plaid_api.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)



#root route
@app.get("/")
def root():
    return {"message": "backend running"}


#creates a link token 
@app.post("/create_link_token")
def create_link_token():
    request = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id="armaan_id"),
        client_name="Net Worth Dashboard",
        products=[Products("transactions")],
        country_codes=[CountryCode("US")],
        language="en",
    )
    response = client.link_token_create(request)
    return response.to_dict()



#automatically validate and parse incoming request data
class PublicTokenRequest(BaseModel):
    public_token: str
    
class AccessTokenRequest(BaseModel):
    access_token: str

def get_db():
    conn = sqlite3.connect("/Users/armaanpatel/Documents/Development/net_worth/netWorthDatabase.db", check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()

# Exchange public token for access token
#this only happens when we add NEW account --> add all accounts to database
@app.post("/exchange_public_token")
def exchange_token(data: PublicTokenRequest, db: sqlite3.Connection = Depends(get_db)):
    request = ItemPublicTokenExchangeRequest(public_token=data.public_token)
    response = client.item_public_token_exchange(request)
    insert_tokens(db, response.item_id, response.access_token, response.request_id)
    update_accounts(response.access_token, db)
    
    return {"Status": "Success"}


def update_accounts(access_token: str, db: sqlite3.Connection):
    request = AccountsBalanceGetRequest(access_token=access_token)
    response = client.accounts_balance_get(request)
    accounts = response.get('accounts', [])
    for account in accounts:
        account_id = account.get('account_id')
        name = account.get('name')
        official_name = account.get('official_name')
        subtype = str(account.get('subtype')) if account.get('subtype') is not None else None
        type_ = str(account.get('type')) if account.get('type') is not None else None
        institution_id = account.get('institution_id')  # May be None
        balances = account.get('balances', {}).get('current')
        request_id = account.get('request_id')

        insert_accounts(db, account_id, access_token, name, official_name, subtype, type_,
                        institution_id, request_id, balances)


#get accounts via tokens and update
@app.post("/accounts/balance")
def update_all_accounts_balances(db: sqlite3.Connection = Depends(get_db)):
    # Get all stored access_tokens from the database
    tokens = get_tokens(db)

    if len(tokens) == 0:
        return {"status": "No account connected"}
    
    for access_token in tokens:
        
        # Fetch the latest balances from Plaid using the access_token
        
        # Extract balances from response and update the accounts table
        update_accounts(access_token ,db)    
    return {"status": "Balances updated successfully"}

# #get tokens from database
# @app.get("/get_tokens")
# def get_tokens_route(db: sqlite3.Connection = Depends(get_db)):
#     result = get_tokens(db)
#     return {"tokens" : result} 

#get accounts from database
@app.get("/accounts")
def get_saved_accounts(db: sqlite3.Connection = Depends(get_db)):
    res = get_accounts(db)
    return res



from fastapi import APIRouter, Depends
import sqlite3
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.transactions_sync_response import TransactionsSyncResponse

@app.post("/syncTransactions")
def sync_transactions(db: sqlite3.Connection = Depends(get_db)):
    tokens = get_transaction_tokens(db)  # [{'token': '...'}]
    
    for token_dict in tokens:
        access_token = decrypt_token(token_dict["token"])
        cursor_value = get_last_cursor(db, access_token)

        has_more = True
        all_transactions = []

        while has_more:
            if cursor_value is not None:
                request = TransactionsSyncRequest(
                    access_token=access_token,
                    cursor=cursor_value
                )
            else: 
                request = TransactionsSyncRequest(
                    access_token=access_token,
                )

            response: TransactionsSyncResponse = client.transactions_sync(request)
            new_transactions = response['added']

            # FILTER: Skip credit card payments from checking accounts
            filtered_transactions = []
            for txn in new_transactions:
                category_group = txn.get('category_group', '')
                category = txn.get('category', [])
                if category_group == "LOAN_PAYMENTS" and "Payment, Credit Card" in category:
                    continue  # skip this transaction
                filtered_transactions.append(txn)

            all_transactions.extend(filtered_transactions)

            cursor_value = response['next_cursor']
            has_more = response['has_more']

        insert_transactions(db, all_transactions)
        update_cursor(db, encrypt_token(access_token), cursor_value)

    return {"message": "Transactions synced and stored successfully"}

@app.get("/transactions/spending_breakdown")
def get_spending_breakdown(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT industry, ROUND(SUM(amount),2) as total
        FROM transactions
        WHERE amount > 0  
        GROUP BY category
    """)
    rows = cursor.fetchall()

    result = [{"category": row[0], "total": row[1]} for row in rows]
    return {"spending": result}
