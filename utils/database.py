import sqlite3
from datetime import datetime
import pandas as pd

DB_NAME = "finance_bot.db"


# =========================================================
# INIT DATABASE
# =========================================================
def init_db():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    # =====================================================
    # USERS TABLE
    # =====================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        username TEXT
    )
    """)

    # =====================================================
    # PORTFOLIOS TABLE
    # =====================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS portfolios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        portfolio_data TEXT,
        created_at TEXT
    )
    """)

    # =====================================================
    # CHATS TABLE
    # =====================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        role TEXT,
        message TEXT,
        created_at TEXT
    )
    """)

    conn.commit()

    conn.close()


# =========================================================
# SAVE USER
# =========================================================
def save_user(user_id, username):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR REPLACE INTO users (
        user_id,
        username
    )
    VALUES (?, ?)
    """, (
        str(user_id),
        username
    ))

    conn.commit()

    conn.close()


# =========================================================
# SAVE PORTFOLIO
# =========================================================
def save_portfolio(user_id, df):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    portfolio_json = df.to_json()

    cursor.execute("""
    INSERT INTO portfolios (
        user_id,
        portfolio_data,
        created_at
    )
    VALUES (?, ?, ?)
    """, (
        str(user_id),
        portfolio_json,
        datetime.now().isoformat()
    ))

    conn.commit()

    conn.close()


# =========================================================
# GET LATEST PORTFOLIO
# =========================================================
def get_latest_portfolio(user_id):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
    SELECT portfolio_data
    FROM portfolios
    WHERE user_id = ?
    ORDER BY id DESC
    LIMIT 1
    """, (
        str(user_id),
    ))

    row = cursor.fetchone()

    conn.close()

    if row:

        return pd.read_json(row[0])

    return None


# =========================================================
# SAVE CHAT
# =========================================================
def save_chat(user_id, role, message):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO chats (
        user_id,
        role,
        message,
        created_at
    )
    VALUES (?, ?, ?, ?)
    """, (
        str(user_id),
        role,
        message,
        datetime.now().isoformat()
    ))

    conn.commit()

    conn.close()


# =========================================================
# GET CHAT HISTORY
# =========================================================
def get_chat_history(user_id, limit=10):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
    SELECT role, message
    FROM chats
    WHERE user_id = ?
    ORDER BY id DESC
    LIMIT ?
    """, (
        str(user_id),
        limit
    ))

    rows = cursor.fetchall()

    conn.close()

    rows.reverse()

    history = []

    for role, message in rows:

        history.append({
            "role": role,
            "message": message
        })

    return history