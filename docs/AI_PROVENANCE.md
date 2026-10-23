# AI assistance and provenance

Date: October 23, 2026. Project: FixTrack, Group G4.

## Inputs and authorization

The user asked ChatGPT/Codex to build the initial project phase for the October 24 Preliminary Design Review and push it to `Jashwanth248/FixTrack_2026`. Inputs included the project context, the October 17 generated SRS draft, the review announcement, and the team's roles. No real university integration or real personal maintenance records were supplied.

## AI-generated work

OpenAI ChatGPT/Codex generated application code, migrations, local styling, the review page, an architecture SVG, seed data, tests, setup instructions and this documentation. It translated the existing SRS draft into repository Markdown. These materials must not be described as independently human-authored code.

## Checks and corrections

Automated checks exercise the core workflow, invalid inputs, role boundaries, stale updates, CSRF, escaped text, login throttling, logout/idle expiry, and rollback after a simulated persistence failure. Migrations and Django system checks are also run. Browser checks and exact results are recorded in VERIFICATION.md. Code was inspected for centralized permission checks, atomic request/history changes and excluded runtime secrets.

The initial local browser installer returned invalid archives. A compatible pinned browser-testing tool was used for visual verification; this tool is not a runtime application dependency. Actual user usability, production TLS, full load testing and human team approval are not claimed.

## Human review still required

Keerthi reviews scope and interface decisions; Jashwanth reviews backend/data rules; Meghdeep reviews requirements and test evidence. These are proposed review responsibilities, not a claim that reviews have occurred. Record names, date, changes and approval after review. All team members should be able to explain the implementation they present.

## Reference

OpenAI. (2026). *ChatGPT* [Large language model]. https://chatgpt.com/

Django Software Foundation. (n.d.). *Django 5.2 documentation*. https://docs.djangoproject.com/en/5.2/
