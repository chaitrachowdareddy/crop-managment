"""Create/reset AgriChain demo accounts in the configured MySQL database."""

import ast
import sys
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

from database.db import USE_CONNECTOR, get_db_connection


DEMO_PASSWORD = "password123"
DEMO_USERS = (
    ("admin", "admin", None),
    ("farmer1", "farmer", 1),
    ("distributor1", "distributor", 1),
    ("retailer1", "retailer", 1),
    ("customer1", "customer", 1),
)

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'farmer', 'distributor', 'retailer', 'customer') NOT NULL,
    entity_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB
"""


def _is_password_hash_field(node):
    return (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id == "user"
        and isinstance(node.slice, ast.Constant)
        and node.slice.value == "password_hash"
    )


def verify_login_password_check(app_path):
    """Ensure the /login route validates the submitted password against its hash."""
    tree = ast.parse(app_path.read_text(encoding="utf-8"), filename=str(app_path))

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or node.name != "login":
            continue

        is_login_route = any(
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and decorator.func.attr == "route"
            and decorator.args
            and isinstance(decorator.args[0], ast.Constant)
            and decorator.args[0].value == "/login"
            for decorator in node.decorator_list
        )
        if not is_login_route:
            continue

        for call in ast.walk(node):
            if (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Name)
                and call.func.id == "check_password_hash"
                and len(call.args) >= 2
                and _is_password_hash_field(call.args[0])
                and isinstance(call.args[1], ast.Name)
                and call.args[1].id == "password"
            ):
                return

    raise RuntimeError(
        "Could not verify check_password_hash(user['password_hash'], password) "
        "inside the /login route in app.py."
    )


def _generate_demo_rows():
    rows = []
    for username, role, entity_id in DEMO_USERS:
        rows.append(
            (
                username,
                generate_password_hash(DEMO_PASSWORD),
                role,
                entity_id,
            )
        )
    return rows


def setup_users():
    project_root = Path(__file__).resolve().parent
    verify_login_password_check(project_root / "app.py")
    rows = _generate_demo_rows()

    connection = get_db_connection(use_database=True)
    cursor = None
    try:
        cursor = (
            connection.cursor(dictionary=True)
            if USE_CONNECTOR
            else connection.cursor()
        )
        cursor.execute(CREATE_USERS_TABLE)

        if USE_CONNECTOR:
            connection.start_transaction()
        else:
            connection.begin()
        try:
            cursor.execute("DELETE FROM users")
            cursor.executemany(
                """
                INSERT INTO users (username, password_hash, role, entity_id)
                VALUES (%s, %s, %s, %s)
                """,
                rows,
            )

            cursor.execute(
                "SELECT username, password_hash, role, entity_id FROM users "
                "ORDER BY user_id"
            )
            seeded_users = cursor.fetchall()
            if len(seeded_users) != len(DEMO_USERS):
                raise RuntimeError(
                    f"Expected {len(DEMO_USERS)} demo accounts, found {len(seeded_users)}."
                )

            for seeded_user, (username, role, entity_id) in zip(seeded_users, DEMO_USERS):
                if (
                    seeded_user["username"] != username
                    or seeded_user["role"] != role
                    or seeded_user["entity_id"] != entity_id
                    or not check_password_hash(
                        seeded_user["password_hash"], DEMO_PASSWORD
                    )
                ):
                    raise RuntimeError(f"Verification failed for account {username!r}.")

            connection.commit()
        except Exception:
            connection.rollback()
            raise
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()

    print("Authentication setup complete. /login password-hash check verified.")
    print("Demo accounts (development use only):")
    print(f"{'Username':<16} {'Password':<16} {'Role':<14} {'Entity ID'}")
    print("-" * 58)
    for username, role, entity_id in DEMO_USERS:
        print(f"{username:<16} {DEMO_PASSWORD:<16} {role:<14} {entity_id}")


if __name__ == "__main__":
    try:
        setup_users()
    except Exception as error:
        print(f"Authentication setup failed: {error}", file=sys.stderr)
        print(
            "Check .env database settings and ensure the schema and referenced "
            "farmer/distributor/retailer/customer records exist.",
            file=sys.stderr,
        )
        raise SystemExit(1) from error
