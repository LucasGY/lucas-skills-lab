---
name: index-valuation-mariadb-import
description: Import wide CSV index valuation history into MariaDB 10 as incremental records in the index_valuation table. Use this when the user provides a CSV like tmp/Data View Export.csv and wants trade_date, index_name, and pe_ntm inserted without reloading existing date plus index rows.
---

# Index Valuation MariaDB Import

Use this skill when the user wants to import a CSV like `tmp/Data View Export.csv` into MariaDB.

## Input CSV shape

The CSV is a wide table:

- first column: `Date`
- remaining columns: index names such as `S&P 500 - PE - NTM`
- each cell value: `PE NTM`

Example mapping:

- CSV `Date` -> database `trade_date`
- CSV header text -> database `index_name`
- CSV cell numeric value -> database `pe_ntm`

## Date handling

- input date format: `DD/MM/YYYY`
- database date format: `YYYY-MM-DD`

## Incremental behavior

The table primary key is `(trade_date, index_name)`.

This skill uses `INSERT IGNORE` so existing rows are skipped automatically and only new date plus index combinations are inserted.

## Required environment variables

- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`

## Script

- `scripts/import_index_valuation_csv.py`

## Commands

Dry run the CSV parse without writing to the database:

```bash
python skills/index-valuation-mariadb-import/scripts/import_index_valuation_csv.py \
  --csv-path "tmp/Data View Export.csv" \
  --dry-run
```

Import into MariaDB:

```bash
export DB_HOST=www.lucasgy.space
export DB_PORT=3307
export DB_USER=finance
export DB_PASSWORD='your-password'
export DB_NAME=finance

python skills/index-valuation-mariadb-import/scripts/import_index_valuation_csv.py \
  --csv-path "tmp/Data View Export.csv"
```
