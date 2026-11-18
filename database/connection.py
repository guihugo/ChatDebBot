import sqlite3
import json
import logging
import uuid
from os import getenv


DATABASE_PATH = getenv("DATABASE_PATH", "deb_bot.db")
logger = logging.getLogger(__name__)


def initialize_database():
    con = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = con.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL UNIQUE,
                sender_id TEXT NOT NULL,
                sender_phone_number TEXT NOT NULL,
                message_text TEXT NOT NULL,
                processing_status TEXT NOT NULL DEFAULT 'received',
                processing_started_at DATETIME,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        message_columns = {
            row[1] for row in cursor.execute("PRAGMA table_info(messages)")
        }
        if "processing_status" not in message_columns:
            cursor.execute(
                "ALTER TABLE messages ADD COLUMN processing_status "
                "TEXT NOT NULL DEFAULT 'received'"
            )
        if "processing_started_at" not in message_columns:
            cursor.execute(
                "ALTER TABLE messages ADD COLUMN processing_started_at DATETIME"
            )
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS debts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        owner_phone_number TEXT,
                        debtor_name TEXT NOT NULL,
                        amount REAL NOT NULL,
                        due_date DATE NOT NULL,
                        description TEXT,
                        status TEXT NOT NULL,
                        reminder_sent INTEGER NOT NULL DEFAULT 0,
                        source_message_id TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )        
        """)
        debt_columns = {
            row[1] for row in cursor.execute("PRAGMA table_info(debts)")
        }
        if "owner_phone_number" not in debt_columns:
            cursor.execute(
                "ALTER TABLE debts ADD COLUMN owner_phone_number TEXT"
            )
        if "reminder_sent" not in debt_columns:
            cursor.execute(
                "ALTER TABLE debts ADD COLUMN reminder_sent INTEGER NOT NULL DEFAULT 0"
            )
        if "description" not in debt_columns:
            cursor.execute("ALTER TABLE debts ADD COLUMN description TEXT")
        if "source_message_id" not in debt_columns:
            cursor.execute("ALTER TABLE debts ADD COLUMN source_message_id TEXT")
        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_debts_source_message_id
            ON debts(source_message_id)
            WHERE source_message_id IS NOT NULL
            """
        )
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS pending_debts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sender_phone_number TEXT NOT NULL UNIQUE,
                        debtor_name TEXT NOT NULL,
                        amount REAL NOT NULL,
                        due_date DATE NOT NULL,
                        description TEXT,
                        confirmation_token TEXT NOT NULL,
                        source_message_id TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
        """)
        pending_debt_columns = {
            row[1] for row in cursor.execute("PRAGMA table_info(pending_debts)")
        }
        if "description" not in pending_debt_columns:
            cursor.execute(
                "ALTER TABLE pending_debts ADD COLUMN description TEXT"
            )
        if "confirmation_token" not in pending_debt_columns:
            cursor.execute(
                "ALTER TABLE pending_debts ADD COLUMN confirmation_token TEXT"
            )
        if "source_message_id" not in pending_debt_columns:
            cursor.execute(
                "ALTER TABLE pending_debts ADD COLUMN source_message_id TEXT"
            )
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS pending_actions (
                        sender_phone_number TEXT PRIMARY KEY,
                        action TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
        """)
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS pending_selections (
                        sender_phone_number TEXT PRIMARY KEY,
                        action TEXT NOT NULL,
                        payload TEXT NOT NULL,
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
    con = sqlite3.connect(DATABASE_PATH)
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
        logger.debug(
            "Message already exists",
            extra={"message_id": message_id},
        )
        return False
    finally:
        con.close()


def start_message_processing(
    message_id: str,
    sender_id: str,
    sender_phone_number: str,
    message_text: str,
) -> bool:
    con = sqlite3.connect(DATABASE_PATH)
    try:
        con.execute("BEGIN IMMEDIATE")
        row = con.execute(
            "SELECT processing_status FROM messages WHERE message_id = ?",
            (message_id,),
        ).fetchone()
        if row and row[0] in {"processing", "completed"}:
            con.rollback()
            return False
        if row:
            con.execute(
                """
                UPDATE messages
                SET processing_status = 'processing',
                    processing_started_at = CURRENT_TIMESTAMP
                WHERE message_id = ?
                """,
                (message_id,),
            )
        else:
            con.execute(
                """
                INSERT INTO messages (
                    message_id, sender_id, sender_phone_number, message_text,
                    processing_status, processing_started_at
                )
                VALUES (?, ?, ?, ?, 'processing', CURRENT_TIMESTAMP)
                """,
                (message_id, sender_id, sender_phone_number, message_text),
            )
        con.commit()
        return True
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def finish_message_processing(message_id: str, status: str) -> None:
    if status not in {"completed", "failed"}:
        raise ValueError(f"Invalid message processing status: {status}")
    con = sqlite3.connect(DATABASE_PATH)
    try:
        con.execute(
            """
            UPDATE messages
            SET processing_status = ?, processing_started_at = NULL
            WHERE message_id = ?
            """,
            (status, message_id),
        )
        con.commit()
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
    con = sqlite3.connect(DATABASE_PATH)
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

def save_debt_to_database(
    owner_phone_number: str,
    debtor_name: str,
    amount: float,
    due_date: str,
    status: str,
    description: str | None = None,
    source_message_id: str | None = None,
):
    """
    Saves a debt record to the SQLite database.

    Args:
        debtor_name (str): The name of the debtor.
        amount (float): The amount of the debt.
        due_date (str): The due date of the debt in 'YYYY-MM-DD' format.
        status (str): The status of the debt (e.g., 'pending', 'paid').
    """
    con = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = con.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO debts (
                owner_phone_number, debtor_name, amount, due_date, description,
                status, source_message_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                owner_phone_number,
                debtor_name,
                amount,
                due_date,
                description,
                status,
                source_message_id,
            ),
        )
        con.commit()
        return cursor.rowcount == 1
    finally:
        con.close()


def save_pending_debt(
    sender_phone_number: str,
    debtor_name: str,
    amount: float,
    due_date: str,
    description: str | None = None,
    source_message_id: str | None = None,
) -> str:
    """Stores the debt details until the user confirms the action."""
    confirmation_token = uuid.uuid4().hex
    con = sqlite3.connect(DATABASE_PATH)
    try:
        con.execute(
            """
            INSERT INTO pending_debts (
                sender_phone_number, debtor_name, amount, due_date, description,
                confirmation_token, source_message_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(sender_phone_number) DO UPDATE SET
                debtor_name = excluded.debtor_name,
                amount = excluded.amount,
                due_date = excluded.due_date,
                description = excluded.description,
                confirmation_token = excluded.confirmation_token,
                source_message_id = excluded.source_message_id,
                timestamp = CURRENT_TIMESTAMP
            """,
            (
                sender_phone_number,
                debtor_name,
                amount,
                due_date,
                description,
                confirmation_token,
                source_message_id,
            ),
        )
        con.commit()
        return confirmation_token
    finally:
        con.close()


def get_pending_debt(
    sender_phone_number: str,
    confirmation_token: str | None = None,
):
    con = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = con.execute(
            """
            SELECT debtor_name, amount, due_date, description,
                   confirmation_token, source_message_id
            FROM pending_debts
            WHERE sender_phone_number = ?
              AND (? IS NULL OR confirmation_token = ?)
            """,
            (sender_phone_number, confirmation_token, confirmation_token),
        )
        row = cursor.fetchone()
        if not row:
            return None

        return {
            "debtor_name": row[0],
            "amount": row[1],
            "due_date": row[2],
            "description": row[3],
            "confirmation_token": row[4],
            "source_message_id": row[5],
        }
    finally:
        con.close()


def delete_pending_debt(sender_phone_number: str) -> None:
    con = sqlite3.connect(DATABASE_PATH)
    try:
        con.execute(
            "DELETE FROM pending_debts WHERE sender_phone_number = ?",
            (sender_phone_number,),
        )
        con.commit()
    finally:
        con.close()


def save_pending_action(sender_phone_number: str, action: str) -> None:
    con = sqlite3.connect(DATABASE_PATH)
    try:
        con.execute(
            """
            INSERT INTO pending_actions (sender_phone_number, action)
            VALUES (?, ?)
            ON CONFLICT(sender_phone_number) DO UPDATE SET
                action = excluded.action,
                timestamp = CURRENT_TIMESTAMP
            """,
            (sender_phone_number, action),
        )
        con.commit()
    finally:
        con.close()


def get_pending_action(sender_phone_number: str):
    con = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = con.execute(
            """
            SELECT action
            FROM pending_actions
            WHERE sender_phone_number = ?
            """,
            (sender_phone_number,),
        )
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        con.close()


def delete_pending_action(sender_phone_number: str) -> None:
    con = sqlite3.connect(DATABASE_PATH)
    try:
        con.execute(
            "DELETE FROM pending_actions WHERE sender_phone_number = ?",
            (sender_phone_number,),
        )
        con.commit()
    finally:
        con.close()


def save_pending_selection(
    sender_phone_number: str, action: str, payload: dict
) -> None:
    con = sqlite3.connect(DATABASE_PATH)
    try:
        con.execute(
            """
            INSERT INTO pending_selections (
                sender_phone_number, action, payload
            )
            VALUES (?, ?, ?)
            ON CONFLICT(sender_phone_number) DO UPDATE SET
                action = excluded.action,
                payload = excluded.payload,
                timestamp = CURRENT_TIMESTAMP
            """,
            (sender_phone_number, action, json.dumps(payload)),
        )
        con.commit()
    finally:
        con.close()


def get_pending_selection(sender_phone_number: str):
    con = sqlite3.connect(DATABASE_PATH)
    try:
        row = con.execute(
            """
            SELECT action, payload
            FROM pending_selections
            WHERE sender_phone_number = ?
            """,
            (sender_phone_number,),
        ).fetchone()
        if not row:
            return None
        return {"action": row[0], "payload": json.loads(row[1])}
    finally:
        con.close()


def delete_pending_selection(sender_phone_number: str) -> None:
    con = sqlite3.connect(DATABASE_PATH)
    try:
        con.execute(
            "DELETE FROM pending_selections WHERE sender_phone_number = ?",
            (sender_phone_number,),
        )
        con.commit()
    finally:
        con.close()


def get_debtor_names(owner_phone_number: str) -> list[str]:
    con = sqlite3.connect(DATABASE_PATH)
    try:
        rows = con.execute(
            """
            SELECT DISTINCT debtor_name
            FROM debts
            WHERE owner_phone_number = ?
              AND status = 'debt'
            ORDER BY debtor_name
            """,
            (owner_phone_number,),
        ).fetchall()
        return [row[0] for row in rows]
    finally:
        con.close()


def get_debts_from_person(owner_phone_number: str, debtor_name: str):
    """
    Retrieves all debts associated with a specific debtor from the SQLite database.

    Args:
        debtor_name (str): The name of the debtor.

    Returns:
        list: A list of dictionaries containing debt records.
    """
    con = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = con.cursor()
        cursor.execute(
            """
            SELECT id, debtor_name, amount, due_date, description, status, timestamp
            FROM debts
            WHERE owner_phone_number = ?
              AND status = 'debt'
              AND debtor_name = ?
              AND status = 'debt'
        """,
            (owner_phone_number, debtor_name),
        )
        rows = cursor.fetchall()
        debts = [
            {
                "id": row[0],
                "debtor_name": row[1],
                "amount": row[2],
                "due_date": row[3],
                "description": row[4],
                "status": row[5],
                "timestamp": row[6],
            }
            for row in rows
        ]
        return debts
    finally:
        con.close()


def get_open_debts(
    owner_phone_number: str,
    debtor_name: str,
    amount: float | None = None,
):
    con = sqlite3.connect(DATABASE_PATH)
    try:
        query = """
            SELECT id, debtor_name, amount, due_date, description, status, timestamp
            FROM debts
            WHERE owner_phone_number = ?
              AND status = 'debt'
              AND debtor_name = ?
              AND status = 'debt'
        """
        parameters: list = [owner_phone_number, debtor_name]
        if amount is not None:
            query += " AND amount = ?"
            parameters.append(amount)
        query += " ORDER BY due_date, id"
        rows = con.execute(query, parameters).fetchall()
        return [
            {
                "id": row[0],
                "debtor_name": row[1],
                "amount": row[2],
                "due_date": row[3],
                "description": row[4],
                "status": row[5],
                "timestamp": row[6],
            }
            for row in rows
        ]
    finally:
        con.close()


def get_all_debts(owner_phone_number: str):
    """Retrieves every debt owned by the specified user."""
    con = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = con.execute(
            """
            SELECT id, debtor_name, amount, due_date, description, status, timestamp
            FROM debts
            WHERE owner_phone_number = ?
              AND status = 'debt'
            ORDER BY due_date, id
            """,
            (owner_phone_number,),
        )
        return [
            {
                "id": row[0],
                "debtor_name": row[1],
                "amount": row[2],
                "due_date": row[3],
                "description": row[4],
                "status": row[5],
                "timestamp": row[6],
            }
            for row in cursor.fetchall()
        ]
    finally:
        con.close()

def get_debts_ready_for_reminder():
    con = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = con.execute(
            """
            SELECT id, owner_phone_number, debtor_name, amount, due_date, description
            FROM debts
            WHERE status = 'debt'
              AND reminder_sent = 0
              AND due_date <= DATE('now')
              AND owner_phone_number IS NOT NULL
            """
        )
        return [
            {
                "id": row[0],
                "owner_phone_number": row[1],
                "debtor_name": row[2],
                "amount": row[3],
                "due_date": row[4],
                "description": row[5],
            }
            for row in cursor.fetchall()
        ]
    finally:
        con.close()


def mark_reminder_sent(debt_id: int, owner_phone_number: str) -> bool:
    con = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = con.execute(
            """
            UPDATE debts
            SET reminder_sent = 1
            WHERE id = ?
              AND owner_phone_number = ?
              AND status = 'debt'
              AND reminder_sent = 0
            """,
            (debt_id, owner_phone_number),
        )
        con.commit()
        return cursor.rowcount == 1
    finally:
        con.close()


def mark_debt_as_paid(debt_id: int, owner_phone_number: str) -> bool:
    con = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = con.execute(
            """
            UPDATE debts
            SET status = 'paid'
            WHERE id = ?
              AND owner_phone_number = ?
              AND status = 'debt'
            """,
            (debt_id, owner_phone_number),
        )
        con.commit()
        return cursor.rowcount == 1
    finally:
        con.close()