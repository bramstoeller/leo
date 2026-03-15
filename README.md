# LEO - Local Energy Optimizer

Optimize household energy consumption using solar panels, home batteries, and a
hot water heater. LEO uses dynamic 15-minute energy prices and self-learned
predictions about energy consumption and PV generation to minimize costs and
relieve the electricity grid.

> **Note:** LEO is designed for local energy optimization, not for energy trading.

## Tools

### Export historical price data

Export all available energy prices from a provider to CSV:

```bash
leo_export_prices frank_energie 15 data/frank_energie_prices.csv
```

This binary-searches for the earliest available date and exports all prices at
the given resolution (in minutes) to CSV.

### Convert HomeWizard CSV to standardized format

Convert a HomeWizard P1 meter CSV export:

```bash
leo_convert_readings p1 data/p1-2024-1-01-2024-12-31.csv data/p1-2024.csv
```

Convert a HomeWizard kWh meter CSV export:

```bash
leo_convert_readings kwh data/solar-2024-1-01-2024-12-31.csv data/solar-2024.csv
```

The output CSV has columns: `timestamp_from,timestamp_till,import_kwh,export_kwh`.
Values are converted to joules (SI) at import time.

### Import price data into the database

```bash
leo_import_prices frank_energie data/frank_energie_prices.csv data/leo.db
```

Duplicate records are rejected by default (the entire import is rolled back).
Use `--overwrite` to replace existing records.

### Import energy readings into the database

Import a standardized CSV (as produced by `leo_convert_readings`):

```bash
leo_import_readings homewizard.p1 data/p1-2024.csv data/leo.db
```

Duplicate records are rejected by default (the entire import is rolled back).
Use `--overwrite` to replace existing records:

```bash
leo_import_readings homewizard.p1 data/p1-2024.csv data/leo.db --overwrite
```

## License

MIT
