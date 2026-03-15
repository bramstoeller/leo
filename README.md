# LEO - Local Energy Optimizer

Optimize household energy consumption using solar panels, home batteries, and a
hot water heater. LEO uses dynamic 15-minute energy prices and self-learned
predictions about energy consumption and PV generation to minimize costs and
relieve the electricity grid.

> **Note:** LEO is designed for local energy optimization, not for energy trading.

## Downloading historical price data

Export all available 15-minute energy prices from a provider to CSV:

```bash
leo_export_prices frank_energie 15 data/frank_energie_prices.csv
```

This binary-searches for the earliest available date and exports all prices at the given resolution (in minutes) to CSV.

## License

MIT
