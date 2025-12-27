from dotenv import load_dotenv
load_dotenv()
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
from decimal import Decimal

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    yield

app = FastAPI(title="Banking MCP Server", version="1.0.0", lifespan=lifespan)

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT")
}


class AccountCreate(BaseModel):
    account_holder_name: str
    initial_balance: Decimal = 0.0


class TransactionRequest(BaseModel):
    account_id: int
    amount: Decimal


class AccountResponse(BaseModel):
    account_id: int
    account_holder_name: str
    balance: Decimal
    created_at: datetime


class TransactionResponse(BaseModel):
    transaction_id: int
    account_id: int
    transaction_type: str
    amount: Decimal
    balance_after: Decimal
    timestamp: datetime


def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")


def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                account_id SERIAL PRIMARY KEY,
                account_holder_name VARCHAR(255) NOT NULL,
                balance DECIMAL(15, 2) DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id SERIAL PRIMARY KEY,
                account_id INTEGER REFERENCES accounts(account_id),
                transaction_type VARCHAR(50) NOT NULL,
                amount DECIMAL(15, 2) NOT NULL,
                balance_after DECIMAL(15, 2) NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("Database tables initialized successfully")
    except Exception as e:
        conn.rollback()
        print(f"Error initializing database: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@app.get("/")
async def root():
    return {
        "message": "Banking MCP Server",
        "version": "1.0.0",
        "endpoints": {
            "create_account": "/accounts/create",
            "deposit": "/accounts/deposit",
            "withdraw": "/accounts/withdraw",
            "balance": "/accounts/{account_id}/balance",
            "transactions": "/accounts/{account_id}/transactions"
        }
    }


@app.post("/accounts/create", response_model=AccountResponse)
async def create_account(account: AccountCreate):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        if account.initial_balance < 0:
            raise HTTPException(status_code=400, detail="Initial balance cannot be negative")
        
        cursor.execute("""
            INSERT INTO accounts (account_holder_name, balance)
            VALUES (%s, %s)
            RETURNING account_id, account_holder_name, balance, created_at
        """, (account.account_holder_name, account.initial_balance))
        
        new_account = cursor.fetchone()
        
        if account.initial_balance > 0:
            cursor.execute("""
                INSERT INTO transactions (account_id, transaction_type, amount, balance_after)
                VALUES (%s, %s, %s, %s)
            """, (new_account['account_id'], 'DEPOSIT', account.initial_balance, account.initial_balance))
        
        conn.commit()
        return new_account
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating account: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@app.post("/accounts/deposit")
async def deposit(transaction: TransactionRequest):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        if transaction.amount <= 0:
            raise HTTPException(status_code=400, detail="Deposit amount must be positive")
        
        cursor.execute("SELECT balance FROM accounts WHERE account_id = %s", (transaction.account_id,))
        account = cursor.fetchone()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        new_balance = account['balance'] + transaction.amount
        
        cursor.execute("""
            UPDATE accounts
            SET balance = %s 
            WHERE account_id = %s
        """, (new_balance, transaction.account_id))
        
        cursor.execute("""
            INSERT INTO transactions (account_id, transaction_type, amount, balance_after)
            VALUES (%s, %s, %s, %s)
        """, (transaction.account_id, 'DEPOSIT', transaction.amount, new_balance))
        
        conn.commit()
        
        return {
            "message": "Deposit successful",
            "account_id": transaction.account_id,
            "amount_deposited": transaction.amount,
            "new_balance": new_balance
        }
        
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing deposit: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@app.post("/accounts/withdraw")
async def withdraw(transaction: TransactionRequest):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        if transaction.amount <= 0:
            raise HTTPException(status_code=400, detail="Withdrawal amount must be positive")
        
        cursor.execute("SELECT balance FROM accounts WHERE account_id = %s", (transaction.account_id,))
        account = cursor.fetchone()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        if float(account['balance']) < transaction.amount:
            raise HTTPException(status_code=400, detail="Insufficient funds")
        
        new_balance = account['balance'] - transaction.amount
        
        cursor.execute("""
            UPDATE accounts 
            SET balance = %s 
            WHERE account_id = %s
        """, (new_balance, transaction.account_id))
        
        cursor.execute("""
            INSERT INTO transactions (account_id, transaction_type, amount, balance_after)
            VALUES (%s, %s, %s, %s)
        """, (transaction.account_id, 'WITHDRAWAL', transaction.amount, new_balance))
        
        conn.commit()
        
        return {
            "message": "Withdrawal successful",
            "account_id": transaction.account_id,
            "amount_withdrawn": transaction.amount,
            "new_balance": new_balance
        }
        
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing withdrawal: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@app.get("/accounts/{account_id}/balance")
async def get_balance(account_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("""
            SELECT account_id, account_holder_name, balance, created_at
            FROM accounts
            WHERE account_id = %s
        """, (account_id,))
        
        account = cursor.fetchone()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        return account
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving balance: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@app.get("/accounts/{account_id}/transactions", response_model=List[TransactionResponse])
async def get_transactions(account_id: int, limit: Optional[int] = 10):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("SELECT account_id FROM accounts WHERE account_id = %s", (account_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Account not found")
        
        cursor.execute("""
            SELECT transaction_id, account_id, transaction_type, amount, balance_after, timestamp
            FROM transactions
            WHERE account_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
        """, (account_id, limit))
        
        transactions = cursor.fetchall()
        
        return transactions
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving transactions: {str(e)}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host = os.getenv("HOST"), port = int(os.getenv("PORT")))