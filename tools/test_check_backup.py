"""Tests for tools/check_backup.py (SRS v2.0 NFR-12, check RT-12).

Run from the project root:
    python -m unittest discover -s tools -p "test_*.py" -v

Each bad copy changes exactly one thing, so a test fails only if the checker
misses that one problem. The schema below is copied from the SQL Django's
0001_initial migration produces for these two tables.
"""
import hashlib
import io
import shutil
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import check_backup

TICKET_SQL = (
    'CREATE TABLE "maintenance_ticket" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, '
    '"location" varchar(100) NOT NULL, "category" varchar(20) NOT NULL, "description" text NOT NULL, '
    '"priority" varchar(10) NOT NULL, "status" varchar(20) NOT NULL, "resolution_note" text NOT NULL, '
    '"created_at" datetime NOT NULL, "updated_at" datetime NOT NULL, "resolved_at" datetime NULL, '
    '"version" integer unsigned NOT NULL CHECK ("version" >= 0), "owner_id" bigint NOT NULL, '
    '"worker_id" bigint NULL, CONSTRAINT "positive_ticket_version" CHECK ("version" >= 1))'
)
# Same columns as TICKET_SQL but with no primary key on id (the damaged restore in finding 01).
TICKET_NO_PK_SQL = TICKET_SQL.replace('"id" integer NOT NULL PRIMARY KEY AUTOINCREMENT', '"id" integer NOT NULL')
HISTORY_SQL = (
    'CREATE TABLE "maintenance_history" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, '
    '"action" varchar(40) NOT NULL, "changes" text NOT NULL, "created_at" datetime NOT NULL, '
    '"actor_id" bigint NOT NULL, "ticket_id" bigint NOT NULL)'
)
TICKETS = [
    (1, 'Library Room 204', 'Electrical', 'Projector will not turn on.', 'High', 'assigned', '',
     '2026-11-01 10:00:00', '2026-11-01 11:00:00', None, 2, 1, 4),
    (2, 'Science Hall 110', 'Plumbing', 'Sink is leaking under the counter.', 'Medium', 'submitted', '',
     '2026-11-02 09:00:00', '2026-11-02 09:00:00', None, 1, 2, None),
]
HISTORY = [
    (1, 'Submitted', '{"status": {"old": null, "new": "submitted"}}', '2026-11-01 10:00:00', 1, 1),
    (2, 'Worker assigned', '{"worker_id": {"old": null, "new": 4}}', '2026-11-01 11:00:00', 3, 1),
    (3, 'Submitted', '{"status": {"old": null, "new": "submitted"}}', '2026-11-02 09:00:00', 2, 2),
]


def build_db(path, ticket_sql=TICKET_SQL, history_sql=HISTORY_SQL, tickets=TICKETS, history=HISTORY):
    con = sqlite3.connect(path)
    con.execute(ticket_sql)
    con.execute(history_sql)
    con.executemany(f'INSERT INTO maintenance_ticket VALUES ({",".join("?" * 13)})', tickets)
    con.executemany('INSERT INTO maintenance_history VALUES (?,?,?,?,?,?)', history)
    con.commit()
    con.close()


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class CheckBackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.backup = self.dir / 'backup.sqlite3'
        self.restored = self.dir / 'restored.sqlite3'
        build_db(self.backup)

    def tearDown(self):
        self.tmp.cleanup()

    def test_identical_copy_matches(self):
        shutil.copyfile(self.backup, self.restored)
        self.assertEqual(check_backup.compare(self.backup, self.restored), [])

    def test_changed_priority_same_count_is_mismatch(self):
        # A count-only check would pass: same number of rows, one field changed.
        changed = [TICKETS[0][:4] + ('Low',) + TICKETS[0][5:], TICKETS[1]]
        build_db(self.restored, tickets=changed)
        problems = check_backup.compare(self.backup, self.restored)
        self.assertEqual(len(problems), 1)
        self.assertIn('maintenance_ticket: field values differ, first at id 1', problems[0])

    def test_missing_history_rows_is_mismatch(self):
        build_db(self.restored, history=HISTORY[:2])
        problems = check_backup.compare(self.backup, self.restored)
        self.assertIn('maintenance_history: row count 3 in backup, 2 restored', problems)

    def test_missing_history_table_is_mismatch(self):
        shutil.copyfile(self.backup, self.restored)
        con = sqlite3.connect(self.restored)
        con.execute('DROP TABLE maintenance_history')
        con.commit()
        con.close()
        problems = check_backup.compare(self.backup, self.restored)
        self.assertIn('maintenance_history: expected a table in the restored file, found nothing', problems)

    def test_view_substituted_for_history_table_is_rejected(self):
        # Finding 02: the real table is renamed and a view with the old name returns the same rows.
        shutil.copyfile(self.backup, self.restored)
        con = sqlite3.connect(self.restored)
        con.execute('ALTER TABLE maintenance_history RENAME TO history_moved')
        con.execute('CREATE VIEW maintenance_history AS SELECT * FROM history_moved')
        con.commit()
        same_rows = con.execute('SELECT * FROM maintenance_history ORDER BY id').fetchall()
        con.close()
        self.assertEqual(same_rows, HISTORY)  # the view really does hide the change
        problems = check_backup.compare(self.backup, self.restored)
        self.assertIn('maintenance_history: expected a table in the restored file, found view', problems)

    def test_missing_primary_key_is_mismatch(self):
        # Finding 01: same ids, values and column names, but no primary key on id.
        build_db(self.restored, ticket_sql=TICKET_NO_PK_SQL)
        problems = check_backup.compare(self.backup, self.restored)
        self.assertIn('maintenance_ticket: column definitions differ (name, type, NOT NULL or primary key)', problems)

    def test_same_file_is_input_error(self):
        with self.assertRaises(check_backup.InputError):
            check_backup.compare(self.backup, self.backup)

    def test_nonexistent_input_is_error_and_no_file_is_created(self):
        # Finding 03: sqlite3.connect() would silently create an empty database here.
        missing = self.dir / 'typo.sqlite3'
        with self.assertRaises(check_backup.InputError):
            check_backup.compare(self.backup, missing)
        self.assertFalse(missing.exists())

    def test_inputs_are_not_modified(self):
        shutil.copyfile(self.backup, self.restored)
        before = sha256(self.backup), sha256(self.restored)
        check_backup.compare(self.backup, self.restored)
        self.assertEqual((sha256(self.backup), sha256(self.restored)), before)

    def test_only_allow_listed_tables_reach_sql(self):
        # Finding 04: Bandit B608 flagged the f-string queries. Table names cannot be
        # ? parameters, so _table() must refuse anything outside REQUIRED_TABLES.
        con = check_backup.open_read_only(self.backup)
        try:
            for name in ('maintenance_user', 'maintenance_ticket"; DROP TABLE x; --'):
                with self.assertRaises(ValueError):
                    check_backup.count_rows(con, name)
            self.assertEqual(check_backup.count_rows(con, 'maintenance_ticket'), len(TICKETS))
        finally:
            con.close()

    def test_command_line_exit_codes(self):
        shutil.copyfile(self.backup, self.restored)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(check_backup.main([str(self.backup), str(self.restored)]), 0)
            self.assertEqual(check_backup.main([str(self.backup), str(self.dir / 'none.sqlite3')]), 2)
        build_db(self.dir / 'other.sqlite3', history=HISTORY[:1])
        with redirect_stdout(io.StringIO()):
            self.assertEqual(check_backup.main([str(self.backup), str(self.dir / 'other.sqlite3')]), 1)


if __name__ == '__main__':
    unittest.main()
