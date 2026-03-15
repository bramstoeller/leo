"""SQLite database access for LEO."""

from pathlib import Path

import aiosqlite

_SCHEMA = """
CREATE TABLE IF NOT EXISTS energy_prices (
    provider_id TEXT NOT NULL,
    timestamp_from TEXT NOT NULL,
    timestamp_till TEXT NOT NULL,
    amount REAL NOT NULL,
    currency TEXT NOT NULL,
    energy_unit TEXT NOT NULL,
    PRIMARY KEY (provider_id, timestamp_from)
);

CREATE TABLE IF NOT EXISTS energy_readings (
    sensor_id TEXT NOT NULL,
    timestamp_from TEXT NOT NULL,
    timestamp_till TEXT NOT NULL,
    import_total REAL NOT NULL,
    import_l1 REAL,
    import_l2 REAL,
    import_l3 REAL,
    export_total REAL NOT NULL,
    export_l1 REAL,
    export_l2 REAL,
    export_l3 REAL,
    unit TEXT NOT NULL,
    PRIMARY KEY (sensor_id, timestamp_from)
);
"""


async def connect(path: Path) -> aiosqlite.Connection:
    """Open a connection and ensure the schema exists."""
    db = await aiosqlite.connect(path)
    await db.executescript(_SCHEMA)
    return db
