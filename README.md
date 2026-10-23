# FixTrack

A campus maintenance request prototype for MSCS 2101, Group G4.

**Preliminary Design Review — October 24, 2026.** This is an initial working prototype, not a production service. Use fictional data only.

## Start here for class

1. Run the app using the instructions below.
2. Open **http://127.0.0.1:8000/review/** for the presentation page: proposal, initial architecture, SRS overview, roles, risk, and questions.
3. Follow [the live demo guide](docs/DEMO.md) to show a complete repair workflow.
4. Use [the SRS](docs/SRS_V1.md), [architecture](docs/ARCHITECTURE.md), and [requirement status](docs/TRACEABILITY.md) for Q&A.

## Run on macOS or Linux

Requires Python 3.12+ and Git. No Node, cloud account, or external API is required.

```bash
git clone https://github.com/Jashwanth248/FixTrack_2026.git
cd FixTrack_2026
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 127.0.0.1:8000
```

Open **http://127.0.0.1:8000**. The seed command prints a generated password; keep it locally. All five demo accounts use it. You can instead supply your own 12+ character password in the `FIXTRACK_DEMO_PASSWORD` environment variable before running the seed command. Never use a real university password.

Windows: use `py -3.12 -m venv .venv`, then `.venv\Scripts\activate`, followed by the same `python` commands.

| Username | Role | Demo purpose |
|---|---|---|
| student | Requester | Submit and track own reports |
| student2 | Requester | Demonstrate another student's access restrictions |
| admin | Administrator | See all requests, assign workers, set priority |
| worker | Worker | Start and resolve assigned work |
| worker2 | Worker | Demonstrate unassigned-worker restrictions |

`admin` is an application role, not a Django superuser. Five sample reports include all four workflow states. The seed command refuses to overwrite existing accounts. For a fresh disposable demo, stop the server, rename `db.sqlite3` to a backup outside this repository, then run migrate and seed again. Do not reset during a presentation or while another person is using the app.

After initial installation, the app runs offline: styles and diagrams are bundled locally. Start the server again with the virtual environment active on presentation day. Django's development server is for localhost only; do not expose this demo to the internet.

## What works

- Requester, administrator, and worker access.
- Reports with required location, category, and description.
- Dashboards, three combined filters, and 20-row pagination.
- Assignment/reassignment, priority, start work, and resolution notes.
- Recorded history, server-side access control, and stale-form rejection.
- CSRF protection, escaped user text, password hashing, idle-session timeout, and persistent basic login throttling.

The state sequence is **Submitted → Assigned → In Progress → Resolved**. Only the current assigned worker can start or resolve. An administrator can reassign unresolved work but cannot resolve it. Resolved requests are read-only.

## Verify

```bash
python manage.py test
python manage.py check
python manage.py makemigrations --check --dry-run
```

See [verification evidence](docs/VERIFICATION.md) for executed checks and remaining quality targets. Tests use a temporary database and do not modify your demo data.

## Team

| Member | Roles |
|---|---|
| Shiva Keerthi Putluri | Project Manager / Leader; UI/UX Designer; Software Engineer / Programmer |
| Jashwanth Bheema | Assistant Project Manager; Software Engineer / Programmer |
| Meghdeep Jana | Quality Assurance & Documentation; Software Engineer / Programmer |

## Scope and AI disclosure

Photos, email, SSO, reopening, public account registration, and production deployment are outside this phase. Team review of generated work is pending. [AI provenance](docs/AI_PROVENANCE.md) records assistance and review limitations. The project is a course demonstration and has no university endorsement or integration.
