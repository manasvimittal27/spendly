import os
import sqlite3
from datetime import date

from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "expense_tracker.db",
)

CATEGORIES = [
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
]


def get_db():
    """Return a SQLite connection with row access by name and foreign keys on."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables. Safe to call repeatedly."""
    conn = get_db()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT    NOT NULL,
                email         TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                created_at    TEXT    DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                amount      REAL    NOT NULL,
                category    TEXT    NOT NULL,
                date        TEXT    NOT NULL,
                description TEXT,
                created_at  TEXT    DEFAULT (datetime('now'))
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def seed_db():
    """Insert a demo user and 8 sample expenses. No-op if users already exist."""
    init_db()
    conn = get_db()
    try:
        has_users = conn.execute("SELECT 1 FROM users LIMIT 1").fetchone()
        if has_users:
            return

        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
        )
        user_id = cur.lastrowid

        # Spread expenses across the current month. Days are capped at 28 so
        # every date is valid regardless of the month.
        today = date.today()
        day = lambda d: date(today.year, today.month, d).isoformat()  # noqa: E731

        samples = [
            (450.00, "Food", day(1), "Groceries"),
            (120.00, "Transport", day(4), "Metro card recharge"),
            (1499.00, "Bills", day(7), "Electricity bill"),
            (680.00, "Health", day(10), "Pharmacy"),
            (350.00, "Entertainment", day(13), "Movie tickets"),
            (899.00, "Shopping", day(16), "Running shoes"),
            (75.00, "Other", day(19), "Stationery"),
            (210.00, "Food", day(22), "Dinner with friends"),
        ]
        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            [(user_id, amt, cat, d, desc) for amt, cat, d, desc in samples],
        )
        conn.commit()
    finally:
        conn.close()
