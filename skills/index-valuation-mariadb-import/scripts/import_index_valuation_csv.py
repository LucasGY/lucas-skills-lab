#!/usr/bin/env python3
import argparse
import csv
import json
import os
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS `index_valuation` (
  `trade_date` DATE NOT NULL COMMENT '交易日期',
  `index_name` VARCHAR(150) NOT NULL COMMENT '原始指数名称，如 S&P 500 / Information Technology - SEC - PE - NTM',
  `pe_ntm` DECIMAL(8,4) DEFAULT NULL COMMENT '未来12个月市盈率 (PE NTM)',
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
  PRIMARY KEY (`trade_date`, `index_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='指数NTM PE估值历史数据';
""".strip()

INSERT_SQL = """
INSERT IGNORE INTO index_valuation (trade_date, index_name, pe_ntm)
VALUES (%s, %s, %s)
""".strip()

SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ENV_PATH = SKILL_DIR / ".env.local"
DEFAULT_CSV_PATH = Path("tmp/Data View Export.csv")
BATCH_SIZE = 500
MISSING_VALUE_MARKERS = {"", "-", "NA", "N/A", "@NA", "NULL", "NONE"}


def parse_env_file(path):
    values = {}
    if not path.is_file():
        return values

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[key] = value
    return values


def get_config_value(cli_value, env_name, env_values, default=None, cast=None):
    value = cli_value if cli_value is not None else os.getenv(env_name)
    if value is None:
        value = env_values.get(env_name, default)
    if cast is not None and value is not None:
        try:
            return cast(value)
        except ValueError as exc:
            raise SystemExit(f"Invalid value for {env_name}: {value}") from exc
    return value


def parse_args():
    parser = argparse.ArgumentParser(
        description="Import wide index valuation CSV data into MariaDB incrementally."
    )
    parser.add_argument(
        "--csv-path",
        default=str(DEFAULT_CSV_PATH),
        help="Path to the source CSV file.",
    )
    parser.add_argument(
        "--env-file",
        default=str(DEFAULT_ENV_PATH),
        help="Path to the local env file. Defaults to the skill's .env.local.",
    )
    parser.add_argument("--db-host", default=None, help="MariaDB host.")
    parser.add_argument("--db-port", type=int, default=None, help="MariaDB port.")
    parser.add_argument("--db-user", default=None, help="MariaDB user.")
    parser.add_argument("--db-password", default=None, help="MariaDB password.")
    parser.add_argument("--db-name", default=None, help="MariaDB database name.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and summarize the CSV without connecting to MariaDB.",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8-sig",
        help="CSV file encoding. Defaults to utf-8-sig.",
    )
    args = parser.parse_args()

    env_values = parse_env_file(Path(args.env_file))
    args.db_host = get_config_value(args.db_host, "DB_HOST", env_values)
    args.db_port = get_config_value(args.db_port, "DB_PORT", env_values, default=3306, cast=int)
    args.db_user = get_config_value(args.db_user, "DB_USER", env_values)
    args.db_password = get_config_value(args.db_password, "DB_PASSWORD", env_values)
    args.db_name = get_config_value(args.db_name, "DB_NAME", env_values)
    args.env_file = str(Path(args.env_file).resolve())
    return args


def require_pymysql():
    try:
        import pymysql  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "PyMySQL is required. Install it with: python -m pip install PyMySQL"
        ) from exc
    return pymysql


def parse_trade_date(raw_value):
    value = (raw_value or "").strip()
    if not value:
        raise ValueError("missing Date value")
    return datetime.strptime(value, "%d/%m/%Y").date()


def normalize_index_name(raw_value):
    return " ".join((raw_value or "").split())


def parse_pe_ntm(raw_value):
    value = (raw_value or "").strip()
    if value.upper() in MISSING_VALUE_MARKERS:
        return None
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"invalid PE NTM value: {value}") from exc


def load_rows(csv_path, encoding):
    path = Path(csv_path)
    if not path.is_file():
        raise SystemExit(f"CSV file not found: {path}")

    with path.open("r", encoding=encoding, newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not reader.fieldnames[0]:
            raise SystemExit("CSV header is missing or invalid.")

        raw_headers = reader.fieldnames
        value_headers = raw_headers[1:]
        normalized_headers = [normalize_index_name(name) for name in value_headers]

        records = []
        source_row_count = 0
        skipped_blank_cells = 0
        for source_row in reader:
            source_row_count += 1
            trade_date = parse_trade_date(source_row[raw_headers[0]])
            for raw_header, index_name in zip(value_headers, normalized_headers):
                pe_ntm = parse_pe_ntm(source_row.get(raw_header))
                if pe_ntm is None:
                    skipped_blank_cells += 1
                    continue
                records.append((trade_date.isoformat(), index_name, pe_ntm))

    return {
        "csv_path": str(path.resolve()),
        "index_count": len(normalized_headers),
        "source_row_count": source_row_count,
        "record_count": len(records),
        "skipped_blank_cells": skipped_blank_cells,
        "records": records,
        "sample_index_names": normalized_headers[:5],
    }


def validate_db_args(args):
    missing = []
    for field_name in ["db_host", "db_user", "db_password", "db_name"]:
        if not getattr(args, field_name):
            missing.append(field_name.upper())
    if missing:
        raise SystemExit(f"Missing database settings: {', '.join(missing)}")


def chunked(records, size):
    for start in range(0, len(records), size):
        yield records[start : start + size]


def import_records(args, parsed):
    validate_db_args(args)
    pymysql = require_pymysql()
    connection = pymysql.connect(
        host=args.db_host,
        port=args.db_port,
        user=args.db_user,
        password=args.db_password,
        database=args.db_name,
        charset="utf8mb4",
        autocommit=False,
    )
    inserted_rows = 0
    try:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_TABLE_SQL)
            for batch in chunked(parsed["records"], BATCH_SIZE):
                cursor.executemany(INSERT_SQL, batch)
                inserted_rows += cursor.rowcount
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return inserted_rows


def main():
    args = parse_args()
    parsed = load_rows(args.csv_path, args.encoding)
    summary = {
        "csv_path": parsed["csv_path"],
        "env_file": args.env_file,
        "source_row_count": parsed["source_row_count"],
        "index_count": parsed["index_count"],
        "record_count": parsed["record_count"],
        "skipped_blank_cells": parsed["skipped_blank_cells"],
        "sample_index_names": parsed["sample_index_names"],
        "dry_run": args.dry_run,
    }

    if args.dry_run:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return

    inserted_rows = import_records(args, parsed)
    summary["inserted_rows"] = inserted_rows
    summary["skipped_existing_rows"] = parsed["record_count"] - inserted_rows
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
