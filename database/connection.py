import sqlite3


def initialize_database():
    con = sqlite3.connect("deb_bot.db")
    try:
        cursor = con.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL UNIQUE,
                sender_id TEXT NOT NULL,
                sender_phone_number TEXT NOT NULL,
                message_text TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS debts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        debtor_name TEXT NOT NULL,
                        amount REAL NOT NULL,
                        due_date DATE NOT NULL,
                        status TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )        
        """)
        con.commit()
    finally:
        con.close()


def kill_database_connection(con):
    """
    Closes the SQLite database connection.

    Args:
        con (sqlite3.Connection): The SQLite database connection to close.
    """
    if con:
        con.close()


def save_message_to_database(
    message_id: str, sender_id: str, sender_phone_number: str, message_text: str
):
    """
    Saves a message to the SQLite database.

    Args:
        message_id (str): The unique ID of the message.
        sender_id (str): The ID of the sender.
        sender_phone_number (str): The phone number of the sender.
        message_text (str): The content of the message.
    """
    con = sqlite3.connect("deb_bot.db")
    try:
        cursor = con.cursor()
        cursor.execute(
            """
            INSERT INTO messages (message_id, sender_id, sender_phone_number, message_text)
            VALUES (?, ?, ?, ?)
        """,
            (message_id, sender_id, sender_phone_number, message_text),
        )
        con.commit()
        return True
    except sqlite3.IntegrityError:
        print(f"Message with ID {message_id} already exists in the database.")
        return False
    finally:
        con.close()


def is_message_processed(message_id: str) -> bool:
    """
    Checks if a message with the given message_id has already been processed.

    Args:
        message_id (str): The unique ID of the message.

    Returns:
        bool: True if the message has been processed, False otherwise.
    """
    con = sqlite3.connect("deb_bot.db")
    try:
        cursor = con.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) FROM messages WHERE message_id = ?
        """,
            (message_id,),
        )
        count = cursor.fetchone()[0]
        return count > 0
    finally:
        con.close()

def save_debt_to_database(debtor_name: str, amount: float, due_date: str, status: str):
    """
    Saves a debt record to the SQLite database.

    Args:
        debtor_name (str): The name of the debtor.
        amount (float): The amount of the debt.
        due_date (str): The due date of the debt in 'YYYY-MM-DD' format.
        status (str): The status of the debt (e.g., 'pending', 'paid').
    """
    con = sqlite3.connect("deb_bot.db")
    try:
        cursor = con.cursor()
        cursor.execute(
            """
            INSERT INTO debts (debtor_name, amount, due_date, status)
            VALUES (?, ?, ?, ?)
        """,
            (debtor_name, amount, due_date, status),
        )
        con.commit()
    finally:
        con.close()

def get_debts_from_person(debtor_name: str):
    """
    Retrieves all debts associated with a specific debtor from the SQLite database.

    Args:
        debtor_name (str): The name of the debtor.

    Returns:
        list: A list of dictionaries containing debt records.
    """
    con = sqlite3.connect("deb_bot.db")
    try:
        cursor = con.cursor()
        cursor.execute(
            """
            SELECT id, debtor_name, amount, due_date, status, timestamp
            FROM debts
            WHERE debtor_name = ?
        """,
            (debtor_name,),
        )
        rows = cursor.fetchall()
        debts = [
            {
                "id": row[0],
                "debtor_name": row[1],
                "amount": row[2],
                "due_date": row[3],
                "status": row[4],
                "timestamp": row[5],
            }
            for row in rows
        ]
        return debts
    finally:
        con.close()