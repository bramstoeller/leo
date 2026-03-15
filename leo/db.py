"""SQLite database access for LEO."""

from pathlib import Path

import aiosqlite

_SCHEMA = """
CREATE TABLE IF NOT EXISTS providers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS sensors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS energy_prices (
    provider_id INTEGER NOT NULL REFERENCES providers(id),
    timestamp_from TEXT NOT NULL,
    timestamp_till TEXT NOT NULL,
    amount REAL NOT NULL,
    currency TEXT NOT NULL,
    energy_unit TEXT NOT NULL,
    PRIMARY KEY (provider_id, timestamp_from, timestamp_till)
);

CREATE TABLE IF NOT EXISTS energy_readings (
    sensor_id INTEGER NOT NULL REFERENCES sensors(id),
    timestamp_from TEXT NOT NULL,
    timestamp_till TEXT NOT NULL,
    import_total REAL NOT NULL,
    export_total REAL NOT NULL,
    unit TEXT NOT NULL,
    PRIMARY KEY (sensor_id, timestamp_from, timestamp_till)
);
"""


async def connect(path: Path) -> aiosqlite.Connection:
    """Open a connection and ensure the schema exists."""
    db = await aiosqlite.connect(path)
    await db.executescript(_SCHEMA)
    return db


async def get_or_create_provider(db: aiosqlite.Connection, uid: str) -> int:
    """Get or create a provider by uid, return its integer ID."""
    cursor = await db.execute("SELECT id FROM providers WHERE uid = ?", (uid,))
    row = await cursor.fetchone()
    if row:
        return row[0]  # type: ignore[no-any-return, return-value]
    cursor = await db.execute("INSERT INTO providers (uid) VALUES (?)", (uid,))
    await db.commit()
    return cursor.lastrowid  # type: ignore[no-any-return, return-value]


async def get_or_create_sensor(db: aiosqlite.Connection, uid: str) -> int:
    """Get or create a sensor by uid, return its integer ID."""
    cursor = await db.execute("SELECT id FROM sensors WHERE uid = ?", (uid,))
    row = await cursor.fetchone()
    if row:
        return row[0]  # type: ignore[no-any-return, return-value]
    cursor = await db.execute("INSERT INTO sensors (uid) VALUES (?)", (uid,))
    await db.commit()
    return cursor.lastrowid  # type: ignore[no-any-return, return-value]
