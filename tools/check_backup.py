"""Compare a restored FixTrack SQLite database with its backup.

Supports SRS v2.0 NFR-12 (Recovery, check RT-12): after a restore, request and
history counts and field values must equal the backup. This tool is local only
(ADR-0001: one Django app, SQLite, no network service). It never writes: both
files are opened read-only and the connection is put in query-only mode.

Usage:
    python tools/check_backup.py BACKUP.sqlite3 RESTORED.sqlite3

Exit codes: 0 = match, 1 = mismatch, 2 = input error (missing file, same file,
SQLite too old).
"""
import argparse
import sqlite3
import sys
from pathlib import Path

# Only these two tables are compared. Names are fixed constants, never user input.
REQUIRED_TABLES = ('maintenance_ticket', 'maintenance_history')

# PRAGMA table_list (used to tell a real table from a view) was added in SQLite 3.37.0.
MIN_SQLITE = (3, 37, 0)


class InputError(Exception):
    """The inputs cannot be compared (missing file, same file, old SQLite)."""


def _check_sqlite_version():
    if sqlite3.sqlite_version_info < MIN_SQLITE:
        need = '.'.join(map(str, MIN_SQLITE))
        raise InputError(f'SQLite {need} or newer is required; found {sqlite3.sqlite_version}')


def open_read_only(path):
    """Open an existing SQLite file without any chance of creating or changing it.

    sqlite3.connect(path) silently creates an empty database when the path is
    wrong, so we check the file first and open it with a read-only URI.
    """
    file = Path(path)
    if not file.is_file():
        raise InputError(f'{path}: file not found')
    con = sqlite3.connect(f'{file.resolve().as_uri()}?mode=ro', uri=True)
    con.execute('PRAGMA trusted_schema = OFF')
    con.execute('PRAGMA query_only = ON')
    return con


def _object_type(con, name):
    """Return 'table', 'view', etc. for a name in the main schema, or None."""
    row = con.execute(
        'SELECT type FROM pragma_table_list WHERE schema = ? AND name = ?', ('main', name)
    ).fetchone()
    return row[0] if row else None


def _table(name):
    """Return the quoted, schema-qualified name of an allowed table.

    SQLite cannot take a table name as a ? parameter, so the queries below must
    build the name into the SQL text. This allow-list is what keeps that safe:
    only the two constant names in REQUIRED_TABLES can ever reach a query.
    """
    if name not in REQUIRED_TABLES:
        raise ValueError(f'not an allowed table: {name!r}')
    return f'main."{name}"'


def _columns(con, name):
    # Each row: (cid, name, type, notnull, default, pk). The pk flag catches a
    # restore that kept the data but lost the primary key.
    _table(name)
    return con.execute("SELECT * FROM pragma_table_info(?, 'main')", (name,)).fetchall()


def _rows(con, name):
    # Safe: _table() only returns one of the two allow-listed names (Bandit B608 reviewed).
    sql = f'SELECT * FROM {_table(name)} ORDER BY id'  # nosec B608
    return con.execute(sql).fetchall()


def count_rows(con, name):
    # Safe: _table() only returns one of the two allow-listed names (Bandit B608 reviewed).
    sql = f'SELECT COUNT(*) FROM {_table(name)}'  # nosec B608
    return con.execute(sql).fetchone()[0]


def compare(backup_path, restored_path):
    """Return a list of differences. An empty list means the restore matches."""
    _check_sqlite_version()
    backup_file, restored_file = Path(backup_path), Path(restored_path)
    for path in (backup_file, restored_file):
        if not path.is_file():
            raise InputError(f'{path}: file not found')
    if backup_file.resolve() == restored_file.resolve() or backup_file.samefile(restored_file):
        raise InputError('backup and restored paths are the same file; the comparison would always match')

    problems = []
    backup = open_read_only(backup_file)
    restored = open_read_only(restored_file)
    try:
        for table in REQUIRED_TABLES:
            # 1. Catalog: the name must be a physical table in main, not a view.
            kinds = {'backup': _object_type(backup, table), 'restored': _object_type(restored, table)}
            bad = {side: kind for side, kind in kinds.items() if kind != 'table'}
            if bad:
                for side, kind in bad.items():
                    problems.append(f'{table}: expected a table in the {side} file, found {kind or "nothing"}')
                continue
            # 2. Column definitions, including NOT NULL and primary-key flags.
            if _columns(backup, table) != _columns(restored, table):
                problems.append(f'{table}: column definitions differ (name, type, NOT NULL or primary key)')
                continue
            # 3. Counts, then every field value in id order.
            rows_b, rows_r = _rows(backup, table), _rows(restored, table)
            if len(rows_b) != len(rows_r):
                problems.append(f'{table}: row count {len(rows_b)} in backup, {len(rows_r)} restored')
            elif rows_b != rows_r:
                first = next(i for i, (x, y) in enumerate(zip(rows_b, rows_r)) if x != y)
                problems.append(f'{table}: field values differ, first at id {rows_b[first][0]}')
    finally:
        backup.close()
        restored.close()
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description='Compare a restored FixTrack database with its backup.')
    parser.add_argument('backup')
    parser.add_argument('restored')
    args = parser.parse_args(argv)
    try:
        problems = compare(args.backup, args.restored)
    except InputError as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2
    if problems:
        print('MISMATCH')
        for problem in problems:
            print(f'  - {problem}')
        return 1
    print('MATCH: ' + ', '.join(REQUIRED_TABLES) + ' have the same columns, counts and field values')
    return 0


if __name__ == '__main__':
    sys.exit(main())
