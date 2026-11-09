"""Timed backup-and-restore drill for SRS v2.0 NFR-12 (check RT-12).

Usage (writes stopped, fictional seeded demo database):
    python tools/recovery_drill.py db.sqlite3 [--requests 1000]

What it does:
  1. Opens the given database read-only and copies only its schema (no rows,
     so no password hashes or real data leave the source file).
  2. In a temporary folder, fills that schema with fictional users, N requests
     and one "Submitted" history entry per request.
  3. Makes a backup with SQLite's online backup API, then stops writing.
  4. Timed part: restores the backup into a fresh file, runs SQLite's integrity
     and foreign-key checks, and compares it with tools/check_backup.py.
  5. Confirms the source and backup files were not changed (SHA-256).

Limits: this measures the database part of RT-12 only. It does not time Django
startup, sign-in, or an authenticated page read after the restore. Everything
is written under a temporary folder that is deleted at the end.
"""
import argparse
import hashlib
import json
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

import check_backup

TIME_LIMIT_SECONDS = 600  # NFR-12: restore within 10 minutes
CATEGORIES = ('Electrical', 'Plumbing', 'Furniture', 'HVAC', 'Other')
PRIORITIES = ('Low', 'Medium', 'High')
NOW = '2026-11-07 12:00:00'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def copy_schema(source_path, target_path):
    source = check_backup.open_read_only(source_path)
    statements = source.execute(
        "SELECT sql FROM sqlite_schema WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' "
        "ORDER BY CASE type WHEN 'table' THEN 0 ELSE 1 END, rowid"
    ).fetchall()
    source.close()
    target = sqlite3.connect(target_path)
    for (sql,) in statements:
        target.execute(sql)
    target.commit()
    return target


def fill_fictional_data(con, requests):
    # Unusable password '!' means no account in the drill database can sign in.
    users = [(1, 'drill_requester', 'requester'), (2, 'drill_worker', 'worker')]
    con.executemany(
        'INSERT INTO maintenance_user (id, password, last_login, is_superuser, username, first_name, '
        'last_name, email, is_staff, is_active, date_joined, role) '
        "VALUES (?, '!', NULL, 0, ?, '', '', '', 0, 1, ?, ?)",
        [(uid, name, NOW, role) for uid, name, role in users],
    )
    tickets, history = [], []
    for i in range(1, requests + 1):
        tickets.append((i, f'Drill Building Room {i % 400 + 100}', CATEGORIES[i % 5],
                        f'Fictional drill request number {i}.', PRIORITIES[i % 3], 'submitted', '',
                        NOW, NOW, None, 1, 1, None))
        changes = json.dumps({'status': {'old': None, 'new': 'submitted'}})
        history.append((i, 'Submitted', changes, NOW, 1, i))
    con.executemany(
        'INSERT INTO maintenance_ticket (id, location, category, description, priority, status, '
        'resolution_note, created_at, updated_at, resolved_at, version, owner_id, worker_id) '
        'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', tickets)
    con.executemany(
        'INSERT INTO maintenance_history (id, action, changes, created_at, actor_id, ticket_id) '
        'VALUES (?,?,?,?,?,?)', history)
    con.commit()


def sqlite_copy(source_path, target_path):
    """Copy a database with SQLite's online backup API (sqlite3.Connection.backup)."""
    source = check_backup.open_read_only(source_path)
    target = sqlite3.connect(target_path)
    source.backup(target)
    target.close()
    source.close()


def run(source_path, requests):
    source_hash = sha256(source_path)
    with tempfile.TemporaryDirectory(prefix='fixtrack-drill-') as tmp:
        work = Path(tmp) / 'live.sqlite3'
        backup = Path(tmp) / 'backup.sqlite3'
        restored = Path(tmp) / 'restored.sqlite3'

        con = copy_schema(source_path, work)
        fill_fictional_data(con, requests)
        con.close()
        sqlite_copy(work, backup)  # writes stop here
        backup_hash = sha256(backup)

        start = time.perf_counter()
        sqlite_copy(backup, restored)
        check = check_backup.open_read_only(restored)
        integrity = check.execute('PRAGMA integrity_check').fetchone()[0]
        fk_problems = check.execute('PRAGMA foreign_key_check').fetchall()
        counts = {t: check_backup.count_rows(check, t) for t in check_backup.REQUIRED_TABLES}
        check.close()
        problems = check_backup.compare(backup, restored)
        elapsed = time.perf_counter() - start

        return {
            'sqlite_version': sqlite3.sqlite_version,
            'requests': requests,
            'restored_counts': counts,
            'integrity_check': integrity,
            'foreign_key_problems': len(fk_problems),
            'comparison_problems': problems,
            'restore_and_verify_seconds': round(elapsed, 4),
            'within_limit': elapsed <= TIME_LIMIT_SECONDS,
            'source_unchanged': sha256(source_path) == source_hash,
            'backup_unchanged': sha256(backup) == backup_hash,
            'backup_size_bytes': backup.stat().st_size,
        }


def main(argv=None):
    parser = argparse.ArgumentParser(description='FixTrack NFR-12 backup/restore drill (database part).')
    parser.add_argument('source', help='seeded demo database, used for its schema only')
    parser.add_argument('--requests', type=int, default=1000)
    args = parser.parse_args(argv)
    try:
        result = run(args.source, args.requests)
    except check_backup.InputError as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    passed = (result['integrity_check'] == 'ok' and result['foreign_key_problems'] == 0
              and not result['comparison_problems'] and result['within_limit']
              and result['source_unchanged'] and result['backup_unchanged']
              and all(n == args.requests for n in result['restored_counts'].values()))
    print('DRILL PASSED' if passed else 'DRILL FAILED')
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
