# FixTrack | Module 6 | Group G4 | November 8, 2026

## Can we trust a restored maintenance database?

Implementation increment and code-review log. Team: Shiva Keerthi Putluri (project manager, UI/UX), Jashwanth Bheema (assistant project manager, backend), Meghdeep Jana (QA and documentation).

## 1. Implementation increment

**What we built.** A local restore checker and a timed recovery drill for the SQLite database.

| File | Purpose |
|---|---|
| `tools/check_backup.py` | Compares a restored database with its backup: table type, column definitions (including primary key), row counts, and every field value of `maintenance_ticket` and `maintenance_history`. Opens both files read-only. Exit code 0 match, 1 mismatch, 2 input error. |
| `tools/recovery_drill.py` | Copies only the schema of the seeded demo database, fills a temporary copy with 1,000 fictional requests and 1,000 history entries, backs it up, then times restore plus verification. |
| `tools/test_check_backup.py` | 11 unit tests, each using a bad copy that changes exactly one thing. |
| `.github/workflows/tests.yml`, `requirements-dev.txt` | CI now also runs the tool tests, flake8 on `tools/`, and Bandit (pinned versions). |

**Requirements.** SRS v2.0 NFR-12 Recovery (check RT-12): after a restore, request and history counts and field values must equal the backup, within 10 minutes. This is the database part of SPMP task T13 (backup/restore procedure, owner Jashwanth, reviewer Keerthi), started early. It also supports NFR-06 (no database or secret leaves the machine: the drill copies schema only and writes only to a temporary folder) and NFR-09 (lint and pinned dependencies).

**Architecture fit.** Consistent with ADR-0001 (SRS v2.0, Appendix D): one Django application with SQLite and no extra service. The tools are offline admin scripts. They add no web endpoint, no role, and no runtime dependency (Python standard library `sqlite3` only), so the request path and the permission service are unchanged (ADR-0002 not affected).

**Builds on the initial draft.** The initial draft set the plan for this increment: a read-only checker, the bad-copy cases to test (missing primary key, substituted view, changed priority, missing history, same file, missing input) and a 1,000-request recovery drill. This version carries that plan into the repository under `tools/`, maps it to SRS v2.0 numbering (Recovery is NFR-12), and adds the CI and security-scan results below.

## 2. Code-review log

We reviewed the AI-generated first draft (kept as `docs/evidence/module6/check_backup_first_draft.py`) against SRS v2.0 using the course checklist and our SPMP 7.4 checklist (SRS ID named, negative test included, no raw SQL from user input, no unchecked package, AI use noted).

| # | Checklist area | Finding (failure mode) | Severity | Resolution |
|---|---|---|---|---|
| 01 | Correctness: hard cases | A restore with the same ids, values and column names but **no primary key** on `id` returned a clean match. The draft compared rows only, so it missed the rule that stops duplicate ids later (plausible-but-wrong). | High | Compare `pragma_table_info` (includes the pk flag) before rows. Test: `test_missing_primary_key_is_mismatch`. |
| 02 | Security: unexpected object | We renamed the history table and created a **view** with the old name. The view returned the same rows, so the draft reported a match even though the real table was gone (silent security hole). | High | Check `pragma_table_list`: each name must be a physical `table` in `main`. Test: `test_view_substituted_for_history_table_is_rejected`. |
| 03 | Reality check: API behavior | `sqlite3.connect()` **creates an empty file** when the path is wrong. The draft left a 0-byte `typo.sqlite3` and then crashed with "no such table". Comparing a file to itself also always "matched". (API exists but behaves differently than the code assumed.) | Medium | Check the file exists, open with a `mode=ro` URI and `query_only`, reject the same file, return exit code 2. Tests: `test_nonexistent_input_is_error_and_no_file_is_created`, `test_same_file_is_input_error`, `test_inputs_are_not_modified`. |
| 04 | Security scan | Bandit B608 flagged the f-string SQL. We checked it: table names cannot be `?` parameters in SQLite, and the names come from two constants, so it was not exploitable. But nothing stopped a future caller from passing user text. | Medium | Added a `_table()` allow-list that rejects any other name; kept a reviewed `# nosec B608` on those two lines only. Test: `test_only_allow_listed_tables_reach_sql` (includes an injection string). |
| 05 | Verification: count-only trap | Changing one ticket's priority High to Low keeps the same row count, so a count-only test would pass. | Medium | Verified, not a new defect: the draft already compared rows. Kept `test_changed_priority_same_count_is_mismatch` as a regression test. |

**Detail on finding 01 (the one that would have shipped):**

```python
# First draft: rows only. Same values + missing primary key -> "MATCH"
rows_a = a.execute(f'SELECT * FROM {table} ORDER BY id').fetchall()

# After review: catalog and columns (with pk flag) are checked before rows
if _object_type(restored, table) != 'table': ...
if _columns(backup, table) != _columns(restored, table): ...
```

The draft read cleanly and passed a "copy the file and compare" test. It failed only when we built a bad copy that changed one rule at a time.

## 3. Quality gates

Our gates come from SPMP 5.3.4, 6.3 and 7.4, and SRS v2.0 NFR-09.

| Gate | Result for this increment |
|---|---|
| Human review by a non-author | Meghdeep Jana (QA) reviewed every AI-generated change against the checklist (log above). Jashwanth Bheema (backend) does the backend review before merge to main (SPMP 5.3.4). |
| Tests | Django suite: 23 of 23 pass. Tool tests: 11 of 11 pass. The same 11 tests against the first draft: 2 pass, 5 fail, 4 error (`tests_against_first_draft.txt`). |
| Coverage | `check_backup.py`: 94% (statements and branches). App-wide coverage for NFR-09 (80% of permission, validation, transition code) not measured in this increment. |
| Lint | flake8 7.4.1 on `tools/`: 0 findings. The older app code has 453 style findings (mostly missing whitespace), so NFR-09 "zero linter errors" is **not yet met project-wide**; logged for T11/T14. |
| Security scan | Bandit 1.9.4 on `tools`, `maintenance`, `config`: 0 issues, 2 reviewed suppressions (finding 04). |
| Django checks | `manage.py check`: no issues. `makemigrations --check`: no changes. |
| CI | SPMP 6.3 says CI runs Bandit, and Django's test runner does not discover `tools/`, so the workflow now runs all gates above. All steps passed locally and run on GitHub with the next push. |

**Recovery drill (RT-12, database part).** 1,000 requests and 1,000 history entries. Restore plus integrity check, foreign-key check and full comparison took **0.0116 s**. Integrity `ok`, 0 foreign-key problems, 0 differences, source and backup SHA-256 unchanged, backup size 425,984 bytes. Environment: Linux sandbox, Python 3.10.12, SQLite 3.37.2, 2 CPU cores, about 3 GB RAM (below the 4 GB test setup in SRS 2.1.5), Django 5.2.18 with asgiref 3.12.1 because the pinned 3.13.0 was not available for Python 3.10. One run; the clock excludes data generation and backup creation.

**Decision.** All automated gates pass. Next steps: Jashwanth's backend review and merge to main, then the full RT-12 run in SPMP T13 (restore on a clean install on a second laptop, Django startup, and an authenticated read). Index, trigger and foreign-key definition checks are planned as a follow-up.

## 4. AI assistance and provenance

**Initial draft:** OpenAI ChatGPT/Codex helped design the checker and recovery drill, drafted the regression cases, and prepared the first version of this log. **Revision after review:** Anthropic Claude (Opus 5.5, in Claude Cowork) read the repository, SRS v2.0 and SPMP; implemented the checker, drill, tests and CI change in the repository; ran every check above; and updated this log. Expected results came from NFR-12 and from bad database copies that each change one thing. The team chose the scope, the requirement and the reviewers, and the team reviewed the AI output before including it. Before and after test runs are kept in the evidence folder so a reviewer can see what changed.

## Reproduce

From the project root:

```
python -m unittest discover -s tools -p "test_*.py" -v
python tools/recovery_drill.py db.sqlite3
python -m flake8 --max-line-length 120 tools/
python -m bandit -q -r tools maintenance config -x maintenance/tests.py,tools/test_check_backup.py
```

Evidence files are in `docs/evidence/module6/`. They contain no database, password, or session data.

## References

Anthropic. (2026). *Claude* [Large language model]. https://claude.ai/
OpenAI. (2026). *ChatGPT* [Large language model]. https://chatgpt.com/
Group G4. (2026). *FixTrack SRS v2.0* and *FixTrack SPMP v1.0*. MSCS 2101, Sofia University.
SQLite. (n.d.). *Pragma statements* (table_list, table_info, query_only, trusted_schema) and *URI filenames*. https://www.sqlite.org/
Python Software Foundation. (n.d.). *sqlite3: DB-API 2.0 interface for SQLite databases*. https://docs.python.org/3/library/sqlite3.html
