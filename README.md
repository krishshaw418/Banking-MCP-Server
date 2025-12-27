# Banking MCP Server

A FastAPI web server that provides basic banking operations with PostgreSQL database.

## Features

- ✅ Account Creation/Registration
- ✅ Deposit Money
- ✅ Withdraw Money
- ✅ Check Balance
- ✅ View Transaction History

## Prerequisites

Before running this server, you need:

1. **Python 3.8+** installed on your system
2. **PostgreSQL** database installed and running locally
3. **pip** (Python package installer)

## Setup Instructions

### 1. Install PostgreSQL

If you don't have PostgreSQL installed:

- **Windows/Mac**: Download from [postgresql.org](https://www.postgresql.org/download/)
- **Linux (Ubuntu/Debian)**: 
  ```bash
  sudo apt update
  sudo apt install postgresql postgresql-contrib
  ```

### 2. Create Database

Open PostgreSQL command line (psql) and create a database:

```sql
CREATE DATABASE bank_db;
```

Or use the default PostgreSQL database and just update the DB_CONFIG in the code.

### 3. Install Python Dependencies

Navigate to the project folder and install required packages:

```bash
pip install -r requirements.txt
```

### 4. Configure Database Connection

Edit `src/server.py` and update the `DB_CONFIG` section with your database credentials:

```python
DB_CONFIG = {
    "host": "localhost",
    "database": "bank_db",
    "user": "postgres",        # Your PostgreSQL username
    "password": "password",    # Your PostgreSQL password
    "port": "5432"
}
```

Or set environment variables:
```bash
export DB_HOST=localhost
export DB_NAME=bank_db
export DB_USER=postgres
export DB_PASSWORD=your_password
export DB_PORT=5432
```

## Running the Server

Start the server with:

```bash
python banking_server.py
```

Or using uvicorn directly:

```bash
uvicorn banking_server:app --reload
```

The server will start at: **http://localhost:8080**

## API Endpoints

### 1. Create Account

**POST** `/accounts/create`

Create a new bank account.

**Request Body:**
```json
{
  "account_holder_name": "John Doe",
  "initial_balance": 1000.00
}
```

**Response:**
```json
{
  "account_id": 1,
  "account_holder_name": "John Doe",
  "balance": 1000.00,
  "created_at": "2024-12-27T10:30:00"
}
```

### 2. Deposit Money

**POST** `/accounts/deposit`

Add funds to an account.

**Request Body:**
```json
{
  "account_id": 1,
  "amount": 500.00
}
```

**Response:**
```json
{
  "message": "Deposit successful",
  "account_id": 1,
  "amount_deposited": 500.00,
  "new_balance": 1500.00
}
```

### 3. Withdraw Money

**POST** `/accounts/withdraw`

Remove funds from an account.

**Request Body:**
```json
{
  "account_id": 1,
  "amount": 200.00
}
```

**Response:**
```json
{
  "message": "Withdrawal successful",
  "account_id": 1,
  "amount_withdrawn": 200.00,
  "new_balance": 1300.00
}
```

### 4. Check Balance

**GET** `/accounts/{account_id}/balance`

Get current account balance.

**Example:** `GET /accounts/1/balance`

**Response:**
```json
{
  "account_id": 1,
  "account_holder_name": "John Doe",
  "balance": 1300.00,
  "created_at": "2024-12-27T10:30:00"
}
```

### 5. Transaction History

**GET** `/accounts/{account_id}/transactions?limit=10`

View recent transactions for an account.

**Example:** `GET /accounts/1/transactions?limit=5`

**Response:**
```json
[
  {
    "transaction_id": 3,
    "account_id": 1,
    "transaction_type": "WITHDRAWAL",
    "amount": 200.00,
    "balance_after": 1300.00,
    "timestamp": "2024-12-27T11:00:00"
  },
  {
    "transaction_id": 2,
    "account_id": 1,
    "transaction_type": "DEPOSIT",
    "amount": 500.00,
    "balance_after": 1500.00,
    "timestamp": "2024-12-27T10:45:00"
  }
]
```

## Understanding the Code

### Key Components:

1. **Pydantic Models**: Define the structure of data (like blueprints)
2. **Database Functions**: Handle connections and operations
3. **API Endpoints**: Define what URLs users can access
4. **Error Handling**: Catch and report problems

### How It Works:

1. User sends a request to an endpoint (e.g., create account)
2. FastAPI validates the data using Pydantic models
3. Server connects to PostgreSQL database
4. Database operation is performed (insert, update, select)
5. Result is sent back to the user as JSON
