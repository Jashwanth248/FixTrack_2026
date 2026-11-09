"""FIRST DRAFT, kept only as review evidence. Do not use. See tools/check_backup.py.

This is the AI-generated first version of the restore checker, before code review.
It compares row counts and ordered rows of the two FixTrack tables and nothing else.
The Module 6 review log (docs/MODULE6_CODE_REVIEW.md) explains what it misses.
"""
import sqlite3
import sys

TABLES = ('maintenance_ticket', 'maintenance_history')


class InputError(Exception):
    pass


def compare(original, restored):
    problems = []
    a = sqlite3.connect(original)
    b = sqlite3.connect(restored)
    for table in TABLES:
        rows_a = a.execute(f'SELECT * FROM {table} ORDER BY id').fetchall()
        rows_b = b.execute(f'SELECT * FROM {table} ORDER BY id').fetchall()
        if len(rows_a) != len(rows_b):
            problems.append(f'{table}: row count {len(rows_a)} != {len(rows_b)}')
        elif rows_a != rows_b:
            problems.append(f'{table}: row values differ')
    a.close()
    b.close()
    return problems


if __name__ == '__main__':
    found = compare(sys.argv[1], sys.argv[2])
    print('MATCH' if not found else '\n'.join(found))
    sys.exit(1 if found else 0)
