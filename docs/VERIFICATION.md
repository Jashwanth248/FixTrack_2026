# Initial prototype verification

Executed October 23, 2026. This records development checks, not team acceptance or production certification.

## Automated application checks

Environment: Python 3.12, Django 5.2.18, SQLite.

- `python manage.py test`: **23 tests passed**.
- `python manage.py check`: no issues.
- `python manage.py makemigrations --check --dry-run`: no changes detected.
- Initial migrations and `seed_demo` completed successfully on a new local database.

The test suite covers the complete workflow, role and ownership restrictions, invalid state transitions, inactive accounts, malformed input, filtered pagination, escaped HTML, missing CSRF tokens, login throttling, idle expiry, stale form rejection, and transactional rollback when history persistence fails. Rollback tests inject a database error; they do not simulate a physical disk failure. Stale-update tests are sequential; simultaneous multi-process contention is not measured.

## Browser smoke check

Playwright 1.51.0 with Chromium 134.0.6998.35, using a local Django server and fictional seeded users:

1. Signed in as requester and submitted a new electrical issue.
2. In a separate administrator session, assigned `worker` and raised priority to High.
3. In a separate worker session, started work and resolved it with a repair note.
4. Refreshed the requester page and verified the resolution and five history entries.
5. Confirmed another requester's direct link receives HTTP 403.
6. Checked request-detail screens at 390px width for horizontal overflow.
7. Visually inspected desktop dashboard, review page, and mobile resolved-request page screenshots.

Outcome: passed. A missing full-width plus glyph on the new-request button was replaced with a standard plus. Browser test dependencies are development-only and are not needed to run the application.

## Remaining checks

The SRS's load/latency, timed usability, Firefox, full keyboard accessibility, measured backup/restore, coverage percentage, production HTTPS, and simultaneous-write stress targets remain pending. See TRACEABILITY.md. The CI workflow repeats the three application commands on pushes and pull requests; its remote run result is separate from these local results.
