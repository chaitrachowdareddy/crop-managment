"""
Database Connection & Query Helper Module.
Supports mysql-connector-python and pymysql.
Provides safe parameterized query execution and connection health checks.
"""
import os
import re
from config import Config

# Attempt to import mysql.connector, fallback to pymysql if needed
try:
    import mysql.connector
    from mysql.connector import Error as DBError
    USE_CONNECTOR = True
except ImportError:
    try:
        import pymysql
        import pymysql.cursors
        from pymysql import Error as DBError
        USE_CONNECTOR = False
    except ImportError:
        raise ImportError(
            "Neither mysql-connector-python nor pymysql is installed. "
            "Please run: pip install -r requirements.txt"
        )


def get_db_connection(use_database=True):
    """
    Establishes and returns a database connection.
    If use_database is False, connects to the MySQL server without selecting a specific database.
    """
    db_config = Config.get_db_config()
    host = db_config['host']
    port = db_config['port']
    user = db_config['user']
    password = db_config['password']
    database = db_config['database'] if use_database else None

    if USE_CONNECTOR:
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            autocommit=True
        )
        return conn
    else:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn


def test_connection():
    """
    Tests whether the MySQL database is reachable and the required database exists.
    Returns: (is_connected: bool, message: str, tables_count: int)
    """
    try:
        conn = get_db_connection(use_database=True)
        cursor = conn.cursor(dictionary=True) if USE_CONNECTOR else conn.cursor()
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        cursor.close()
        conn.close()
        return True, "Successfully connected to MySQL database!", len(tables)
    except Exception as e:
        return False, str(e), 0


def execute_query(query, params=None, fetchone=False, fetchall=False, commit=False):
    """
    Executes a SQL query safely using parameterized inputs.
    
    Args:
        query (str): The SQL query with %s placeholders.
        params (tuple/list): Query parameters.
        fetchone (bool): Return single row as dict.
        fetchall (bool): Return all rows as list of dicts.
        commit (bool): Explicitly commit transaction for INSERT/UPDATE/DELETE.
        
    Returns:
        List of dicts, single dict, inserted ID, or rowcount.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection(use_database=True)
        if USE_CONNECTOR:
            cursor = conn.cursor(dictionary=True)
        else:
            cursor = conn.cursor()

        cursor.execute(query, params or ())

        if commit:
            conn.commit()
            last_id = cursor.lastrowid
            row_count = cursor.rowcount
            return last_id if last_id else row_count

        if fetchone:
            return cursor.fetchone()

        if fetchall:
            return cursor.fetchall()

        return True
    except Exception as err:
        if conn and commit:
            conn.rollback()
        raise err
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def run_sql_script(filepath):
    """
    Reads an SQL file and executes its statements against the MySQL server.
    Useful for initializing or resetting the database schema and sample data.
    """
    if not os.path.exists(filepath):
        return False, f"File not found: {filepath}"

    with open(filepath, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    try:
        # First connect without specifying database to allow CREATE DATABASE
        conn = get_db_connection(use_database=False)
        cursor = conn.cursor()

        # Split SQL file statements (handles DELIMITER blocks simply)
        statements = []
        delimiter = ';'
        current_stmt = []

        lines = sql_content.split('\n')
        for line in lines:
            trimmed = line.strip()
            if trimmed.upper().startswith('DELIMITER'):
                parts = trimmed.split()
                if len(parts) > 1:
                    delimiter = parts[1]
                continue
            
            if not trimmed or trimmed.startswith('--') or trimmed.startswith('/*'):
                continue

            current_stmt.append(line)
            if trimmed.endswith(delimiter):
                stmt_str = '\n'.join(current_stmt)
                if delimiter != ';':
                    stmt_str = stmt_str.rstrip(delimiter)
                statements.append(stmt_str)
                current_stmt = []

        for statement in statements:
            stmt = statement.strip()
            if stmt:
                try:
                    cursor.execute(stmt)
                except Exception as sql_err:
                    # Ignore non-fatal warnings
                    print(f"[SQL Script Warning/Notice]: {sql_err}")

        cursor.close()
        conn.close()
        return True, "SQL script executed successfully!"
    except Exception as e:
        return False, f"Failed to execute SQL script: {str(e)}"
