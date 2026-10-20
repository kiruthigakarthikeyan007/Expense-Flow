
import sqlite3
from pathlib import Path

DB_NAME = Path(__file__).parent / "expenses.db"


def get_connection():
    connection = sqlite3.connect(DB_NAME)
    connection.row_factory = sqlite3.Row
    return connection


def create_table():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL CHECK (amount > 0),
                category TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                date TEXT NOT NULL
            )
        """)


def add_expense(amount, category, description, date):
    with get_connection() as connection:
        connection.execute("""
            INSERT INTO expenses (amount, category, description, date)
            VALUES (?, ?, ?, ?)
        """, (amount, category, description, date))


def get_expenses():
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT id, amount, category, description, date
            FROM expenses
            ORDER BY date DESC, id DESC
        """).fetchall()

    return [dict(row) for row in rows]


def delete_expense(expense_id):
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM expenses WHERE id = ?",
            (expense_id,)
        )
