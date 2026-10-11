"""
database/setup_db.py

Database setup utility for Module 2.

Responsibilities:
    1. Connect to the PostgreSQL server.
    2. Create the Module 2 database if it does not exist.
    3. Connect to the Module 2 database.
    4. Apply database/schema.sql.
    5. Verify the required Module 2 tables exist.

Database architecture:

    roads
       |
       v
    road_observations
       |
       v
    road_health_predictions

Configuration is read from .env or environment variables:

    DB_HOST
    DB_PORT
    DB_NAME
    DB_USER
    DB_PASSWORD

Example:

    DB_HOST=localhost
    DB_PORT=5432
    DB_NAME=road_health_db
    DB_USER=postgres
    DB_PASSWORD=your_password

Run from the project root:

    python database/setup_db.py
"""

from __future__ import annotations

import os
from pathlib import Path

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ENV_FILE = PROJECT_ROOT / ".env"

SCHEMA_FILE = Path(__file__).resolve().parent / "schema.sql"

load_dotenv(ENV_FILE)


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

def get_database_host() -> str:
    """
    Return the PostgreSQL server host.
    """
    return os.getenv("DB_HOST", "localhost").strip()


def get_database_port() -> int:
    """
    Return the PostgreSQL server port.
    """

    port = os.getenv("DB_PORT", "5432").strip()

    try:
        return int(port)
    except ValueError as exc:
        raise RuntimeError(
            f"Invalid DB_PORT value: '{port}'. "
            "DB_PORT must be a valid integer."
        ) from exc


def get_database_name() -> str:
    """
    Return the target Module 2 database name.
    """

    database_name = os.getenv(
        "DB_NAME",
        "road_health_db",
    ).strip()

    if not database_name:
        raise RuntimeError(
            "DB_NAME cannot be empty."
        )

    return database_name


def get_database_user() -> str:
    """
    Return the PostgreSQL username.
    """

    database_user = os.getenv(
        "DB_USER",
        "postgres",
    ).strip()

    if not database_user:
        raise RuntimeError(
            "DB_USER cannot be empty."
        )

    return database_user


def get_database_password() -> str:
    """
    Return the PostgreSQL password.

    The password must be supplied through the environment
    or .env file. It is never hardcoded in this source file.
    """

    password = os.getenv("DB_PASSWORD")

    if password is None or not password.strip():
        raise RuntimeError(
            "DB_PASSWORD is not configured. "
            "Set DB_PASSWORD in .env or as an environment variable."
        )

    return password


# ============================================================
# CONNECTION PARAMETERS
# ============================================================

def get_connection_parameters(database_name: str) -> dict:
    """
    Build PostgreSQL connection parameters for a specific database.

    Args:
        database_name:
            PostgreSQL database to connect to.

    Returns:
        dict: psycopg2 connection parameters.
    """

    return {
        "host": get_database_host(),
        "port": get_database_port(),
        "dbname": database_name,
        "user": get_database_user(),
        "password": get_database_password(),
    }


# ============================================================
# CREATE DATABASE
# ============================================================

def create_database_if_missing() -> None:
    """
    Create the Module 2 database if it does not already exist.

    PostgreSQL does not allow CREATE DATABASE inside a normal
    transaction, so the administrative connection uses
    autocommit=True.

    The connection is made to the PostgreSQL maintenance database
    'postgres', because the target database may not exist yet.
    """

    target_database = get_database_name()

    admin_parameters = get_connection_parameters(
        database_name="postgres"
    )

    print(
        f"Connecting to PostgreSQL server "
        f"{admin_parameters['host']}:{admin_parameters['port']}..."
    )

    connection = None
    cursor = None

    try:
        connection = psycopg2.connect(**admin_parameters)

        # CREATE DATABASE must run outside a transaction.
        connection.autocommit = True

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT 1
            FROM pg_database
            WHERE datname = %s;
            """,
            (target_database,),
        )

        database_exists = cursor.fetchone() is not None

        if database_exists:
            print(
                f"Database '{target_database}' already exists."
            )
            return

        print(
            f"Creating database '{target_database}'..."
        )

        cursor.execute(
            sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(target_database)
            )
        )

        print(
            f"Database '{target_database}' created successfully."
        )

    except psycopg2.Error as exc:
        raise RuntimeError(
            "Unable to connect to PostgreSQL or create the "
            f"database '{target_database}': {exc}"
        ) from exc

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# READ SCHEMA
# ============================================================

def read_schema_file() -> str:
    """
    Read database/schema.sql.

    Returns:
        str: Complete SQL schema.

    Raises:
        FileNotFoundError:
            If schema.sql does not exist.
    """

    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(
            f"Database schema file was not found: {SCHEMA_FILE}"
        )

    if not SCHEMA_FILE.is_file():
        raise RuntimeError(
            f"Database schema path is not a file: {SCHEMA_FILE}"
        )

    return SCHEMA_FILE.read_text(
        encoding="utf-8"
    )


# ============================================================
# APPLY DATABASE SCHEMA
# ============================================================

def apply_schema() -> None:
    """
    Apply database/schema.sql to the Module 2 database.

    The schema contains:
        - PostGIS extension
        - roads
        - road_observations
        - road_health_predictions
        - indexes
        - triggers
        - supporting functions
    """

    target_database = get_database_name()

    schema_sql = read_schema_file()

    database_parameters = get_connection_parameters(
        database_name=target_database
    )

    print(
        f"Connecting to database '{target_database}'..."
    )

    connection = None
    cursor = None

    try:
        connection = psycopg2.connect(
            **database_parameters
        )

        cursor = connection.cursor()

        print(
            "Applying database/schema.sql..."
        )

        cursor.execute(schema_sql)

        connection.commit()

        print(
            "Database schema applied successfully."
        )

    except psycopg2.Error as exc:

        if connection is not None:
            connection.rollback()

        raise RuntimeError(
            f"Failed to apply database schema: {exc}"
        ) from exc

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# VERIFY POSTGIS
# ============================================================

def verify_postgis() -> bool:
    """
    Verify that the PostGIS extension is enabled.

    Returns:
        bool: True if PostGIS is installed/enabled.
    """

    target_database = get_database_name()

    database_parameters = get_connection_parameters(
        database_name=target_database
    )

    connection = None
    cursor = None

    try:
        connection = psycopg2.connect(
            **database_parameters
        )

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM pg_extension
                WHERE extname = 'postgis'
            );
            """
        )

        postgis_enabled = cursor.fetchone()[0]

        if postgis_enabled:
            print(
                "PostGIS extension is enabled."
            )
        else:
            print(
                "WARNING: PostGIS extension is not enabled."
            )

        return postgis_enabled

    except psycopg2.Error as exc:
        raise RuntimeError(
            f"Unable to verify PostGIS: {exc}"
        ) from exc

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# VERIFY REQUIRED TABLES
# ============================================================

def verify_required_tables() -> bool:
    """
    Verify that all required Module 2 tables exist.

    Required tables:

        roads
        road_observations
        road_health_predictions

    Returns:
        bool:
            True if all required tables exist.
            False otherwise.
    """

    target_database = get_database_name()

    required_tables = {
        "roads",
        "road_observations",
        "road_health_predictions",
    }

    database_parameters = get_connection_parameters(
        database_name=target_database
    )

    connection = None
    cursor = None

    try:
        connection = psycopg2.connect(
            **database_parameters
        )

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
            """
        )

        existing_tables = {
            row[0]
            for row in cursor.fetchall()
        }

        print(
            f"\nTables found in '{target_database}':"
        )

        for table_name in sorted(existing_tables):
            print(f"  - {table_name}")

        missing_tables = (
            required_tables - existing_tables
        )

        if missing_tables:
            print(
                "\nMissing required Module 2 tables:"
            )

            for table_name in sorted(missing_tables):
                print(f"  - {table_name}")

            return False

        print(
            "\nAll required Module 2 tables are present."
        )

        return True

    except psycopg2.Error as exc:
        raise RuntimeError(
            f"Unable to verify database tables: {exc}"
        ) from exc

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# VERIFY REQUIRED COLUMNS
# ============================================================

def verify_required_columns() -> bool:
    """
    Verify the important columns required by Module 2.

    This provides an additional consistency check between
    schema.sql and api/routes.py.
    """

    target_database = get_database_name()

    required_columns = {
        "roads": {
            "road_id",
            "road_type",
            "road_length_km",
            "road_age_years",
            "lane_count",
        },
        "road_observations": {
            "observation_id",
            "road_id",
            "timestamp",
            "pothole_count",
            "damage_count",
            "damage_type",
            "damage_severity",
            "damaged_area_percent",
            "vehicle_count",
            "confidence_score",
            "rainfall_mm",
            "temperature_c",
            "humidity_pct",
            "weather_condition",
            "days_since_maintenance",
            "maintenance_count_last_year",
            "historical_accident_count",
            "latitude",
            "longitude",
            "geom",
        },
        "road_health_predictions": {
            "prediction_id",
            "road_id",
            "observation_id",
            "prediction_time",
            "health_score",
            "condition",
            "congestion_level",
            "accident_risk",
            "maintenance_priority",
            "latitude",
            "longitude",
            "geom",
            "model_version",
        },
    }

    database_parameters = get_connection_parameters(
        database_name=target_database
    )

    connection = None
    cursor = None

    try:
        connection = psycopg2.connect(
            **database_parameters
        )

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                table_name,
                column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name IN (
                  'roads',
                  'road_observations',
                  'road_health_predictions'
              );
            """
        )

        existing_columns: dict[str, set[str]] = {}

        for table_name, column_name in cursor.fetchall():
            existing_columns.setdefault(
                table_name,
                set(),
            ).add(column_name)

        all_columns_valid = True

        for table_name, expected_columns in required_columns.items():

            actual_columns = existing_columns.get(
                table_name,
                set(),
            )

            missing_columns = (
                expected_columns - actual_columns
            )

            if missing_columns:
                all_columns_valid = False

                print(
                    f"\nMissing columns in '{table_name}':"
                )

                for column_name in sorted(missing_columns):
                    print(
                        f"  - {column_name}"
                    )

        if all_columns_valid:
            print(
                "All required Module 2 columns are present."
            )

        return all_columns_valid

    except psycopg2.Error as exc:
        raise RuntimeError(
            f"Unable to verify database columns: {exc}"
        ) from exc

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# COMPLETE DATABASE VERIFICATION
# ============================================================

def verify_database() -> None:
    """
    Run all database verification checks.
    """

    print("\n" + "=" * 60)
    print("DATABASE VERIFICATION")
    print("=" * 60)

    postgis_ok = verify_postgis()

    tables_ok = verify_required_tables()

    columns_ok = verify_required_columns()

    if not postgis_ok:
        raise RuntimeError(
            "Database verification failed: PostGIS is not enabled."
        )

    if not tables_ok:
        raise RuntimeError(
            "Database verification failed: required tables are missing."
        )

    if not columns_ok:
        raise RuntimeError(
            "Database verification failed: required columns are missing."
        )

    print(
        "\nDatabase verification completed successfully."
    )


# ============================================================
# MAIN SETUP FUNCTION
# ============================================================

def setup_database() -> None:
    """
    Execute the complete Module 2 database setup.
    """

    print("=" * 60)
    print("MODULE 2 — DATABASE SETUP")
    print("=" * 60)

    print(
        f"Project root : {PROJECT_ROOT}"
    )

    print(
        f"Schema file  : {SCHEMA_FILE}"
    )

    print(
        f"Database     : {get_database_name()}"
    )

    print(
        f"Host         : {get_database_host()}"
    )

    print(
        f"Port         : {get_database_port()}"
    )

    print(
        f"User         : {get_database_user()}"
    )

    print("=" * 60)

    # --------------------------------------------------------
    # Step 1
    # Create database if necessary.
    # --------------------------------------------------------

    create_database_if_missing()

    # --------------------------------------------------------
    # Step 2
    # Apply schema.sql.
    # --------------------------------------------------------

    apply_schema()

    # --------------------------------------------------------
    # Step 3
    # Verify database.
    # --------------------------------------------------------

    verify_database()

    print("\n" + "=" * 60)
    print("DATABASE SETUP COMPLETED SUCCESSFULLY")
    print("=" * 60)

    print(
        "\nModule 2 database architecture:"
    )

    print(
        "    roads"
    )

    print(
        "       |"
    )

    print(
        "       v"
    )

    print(
        "    road_observations"
    )

    print(
        "       |"
    )

    print(
        "       v"
    )

    print(
        "    road_health_predictions"
    )

    print(
        "\nYou can now start the API with:"
    )

    print(
        "    uvicorn api.main:app --reload"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    try:
        setup_database()

    except Exception as exc:
        print(
            "\nDATABASE SETUP FAILED"
        )

        print(
            f"Error: {exc}"
        )

        raise SystemExit(1)

