"""
database package for Module 2.

This package contains the PostgreSQL database components
used by the Road Health Prediction System.

Modules:
    connection.py
        Handles PostgreSQL connection, SQLAlchemy engine,
        and database sessions.

    setup_db.py
        Creates the database, applies schema.sql, and
        verifies the required database structure.

    schema.sql
        Defines the roads, road_observations, and
        road_health_predictions tables.

The package initializer intentionally does not connect to
the database or create/drop any tables during import.
"""

__version__ = "1.0.0"