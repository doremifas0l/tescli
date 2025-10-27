
import sqlite3
from datetime import datetime

def get_db_connection():
    conn = sqlite3.connect('finance.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL,
            category TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_transaction(description, amount, type, category):
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO transactions (description, amount, type, category, date) VALUES (?, ?, ?, ?, ?)',
        (description, amount, type, category, datetime.now())
    )
    conn.commit()
    conn.close()

def get_transactions():
    conn = get_db_connection()
    transactions = conn.execute('SELECT * FROM transactions ORDER BY date DESC').fetchall()
    conn.close()
    return transactions
