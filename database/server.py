import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import aiosqlite
import yaml

config = yaml.safe_load(open('../config.yaml', 'r', encoding='utf-8'))

def custom_encoder(obj):
    """
    Custom JSON encoder for objects not serializable by default.

    Converts date and datetime objects to ISO 8601 string format.
    Raises TypeError for unsupported types.
    """
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

class Database:
    """
    Asynchronous SQLite database handler using aiosqlite.

    This class manages a single asynchronous connection to an SQLite database file
    and provides common methods for executing queries, including:

    - Connecting and disconnecting to the database.
    - Fetching a single row or multiple rows.
    - Inserting data and returning the last inserted row ID.
    - Updating or deleting data and returning the count of affected rows.

    Attributes:
        db_path (str): Path to the SQLite database file.
        conn (Optional[aiosqlite.Connection]): The active database connection, or None if disconnected.

    Methods:
        connect(): Asynchronously open a connection to the database.
        disconnect(): Asynchronously close the database connection.
        fetch(query, *args): Execute a query and return a single row as a dictionary.
        fetchmany(query, *args): Execute a query and return multiple rows as a list of dictionaries.
        insert(query, *args): Execute an INSERT query and return the last inserted row ID.
        update(query, *args): Execute an UPDATE or DELETE query and return the number of affected rows.

    Raises:
        RuntimeError: If any method is called before the database connection is established.

    Example:
        ```python
        db = Database("example.db")
        await db.connect()
        user = await db.fetch("SELECT * FROM users WHERE id = ?", user_id)
        await db.disconnect()
        ```
    """

    def __init__(self, db_path: str):
        """
        Initialize Database instance.

        Args:
            db_path (str): Path to SQLite database file.
        """
        self.db_path = db_path
        self.conn: Optional[aiosqlite.Connection] = None


    async def _create_table(self) -> None:
        """
        Create table from SQL file using aiosqlite.

        Reads SQL commands from 'schemas/data.sql' 
            and executes them as a script.
        """
        sql_file = Path(__file__).parent / "schemas" / "data.sql"
        sql = sql_file.read_text(encoding='utf-8')

        async with self.conn.execute("BEGIN"):
            await self.conn.executescript(sql)
        await self.conn.commit()

    async def connect(self) -> None:
        """
        Open SQLite database connection asynchronously.
        """
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row  # return dict-like rows

    async def disconnect(self) -> None:
        """
        Close SQLite database connection asynchronously.
        """
        if self.conn:
            await self.conn.close()
            self.conn = None

    async def fetch(self, query: str, *args) -> Dict[str, Any]:
        """
        Execute a query and fetch a single row as a dictionary.

        Args:
            query (str): SQL query string.
            *args: Parameters for the SQL query.

        Returns:
            Dict[str, Any]: The first row returned by the query as a dict,
                            or an empty dict if no row is found.

        Raises:
            RuntimeError: If the database connection is not initialized.
        """
        if not self.conn:
            raise RuntimeError("Database connection is not initialized.")

        async with self.conn.execute(query, args) as cursor:
            row = await cursor.fetchone()
            if row:
                return json.loads(json.dumps(dict(row), default=custom_encoder))
            return {}

    async def fetchmany(self, query: str, *args) -> List[Dict[str, Any]]:
        """
        Execute a query and fetch multiple rows as a list of dictionaries.

        Args:
            query (str): SQL query string.
            *args: Parameters for the SQL query.

        Returns:
            List[Dict[str, Any]]: List of rows as dictionaries,
                                  or empty list if no rows found.

        Raises:
            RuntimeError: If the database connection is not initialized.
        """
        if not self.conn:
            raise RuntimeError("Database connection is not initialized.")

        async with self.conn.execute(query, args) as cursor:
            rows = await cursor.fetchall()
            return json.loads(
                json.dumps(
                    [dict(row) for row in rows], 
                    default=custom_encoder
                )
                ) if rows else []

    async def insert(self, query: str, *args) -> Dict[str, Any]:
        """
        Execute an INSERT query and return the last inserted row ID.

        Args:
            query (str): SQL INSERT query string.
            *args: Parameters for the SQL query.

        Returns:
            Dict[str, Any]: Dictionary containing the last inserted row ID.

        Raises:
            RuntimeError: If the database connection is not initialized.
        """
        if not self.conn:
            raise RuntimeError("Database connection is not initialized.")

        async with self.conn.execute(query, args) as cursor:
            await self.conn.commit()
            return {"last_row_id": cursor.lastrowid}

    async def update(self, query: str, *args) -> Dict[str, Any]:
        """
        Execute an UPDATE or DELETE query and return affected rows count.

        Args:
            query (str): SQL UPDATE or DELETE query string.
            *args: Parameters for the SQL query.

        Returns:
            Dict[str, Any]: Dictionary containing the number of affected rows.

        Raises:
            RuntimeError: If the database connection is not initialized.
        """
        if not self.conn:
            raise RuntimeError("Database connection is not initialized.")

        async with self.conn.execute(query, args) as cursor:
            await self.conn.commit()
            return {"rows_affected": cursor.rowcount}
