# Class presentation and live demo

Use `/review/` as the presentation page. It presents the proposal, SRS summary, architecture figure, team roles, risk and feedback questions. It also prints from the browser if you want a paper backup. Bring the original proposal and SRS documents as the formal deliverables.

## Suggested speaking responsibilities

These are proposed assignments, not claims about completed individual work.

- **Keerthi:** problem, target users, scope, team roles and why the interface is simple.
- **Jashwanth:** architecture diagram and working request-to-resolution demo.
- **Meghdeep:** test evidence, access restrictions, remaining targets and feedback questions.

The instructor's message gives the class session time, not a team presentation duration. Keep this adaptable to the allotted slot.

## Before class

1. Complete README installation once; write down the generated demo password locally.
2. Run tests. Open `/review/` and confirm the architecture image displays.
3. Start the server before your turn. Keep the terminal running.
4. Have three separate browser profiles ready, or use Sign out between roles. Tabs in one profile share a login session.
5. Use fictional data. Do not reset the database during the demo.

## Live workflow

1. Sign in as `student`. Show the dashboard and the existing states.
2. Select **New request**. Enter `Library Room 204`, category `Electrical`, and `The classroom projector will not turn on.` Submit.
3. Note its FT ID and URL. Explain that status starts at Submitted and priority at Medium.
4. Sign out. Sign in as `admin`, open the same request, select `worker`, and click **Assign worker**. Set priority to High.
5. Sign out. Sign in as `worker`. Open the assigned request and click **Start work**.
6. Enter `Replaced the projector cable and verified the display works.` and click **Resolve request**.
7. Sign back in as `student`; show the resolution note and timestamped history.
8. Sign in as `student2`; paste the request URL. Show the 403 access restriction. Return to the dashboard.
9. Open `/review/` and discuss pending quality measurements and the reopening decision.

## Extra demo if time permits

As admin, open the same unresolved request in two tabs. Change priority in one, then submit the older form in the other. The second update is rejected rather than silently overwriting work. Reload before continuing.

## Answers to likely questions

**Why Django?** It supplies authentication, forms, templates, CSRF protection and database access in one application.

**Why SQLite?** Simple local setup for a small classroom prototype; we must measure load and revisit the database before production use.

**Is it complete?** The core workflow runs. Load, usability participants, broader browser testing, backup/restore measurement and production deployment are still pending.

**What is the biggest risk?** Inconsistent access and state rules. The service centralizes them, and negative tests exercise direct requests.

**How was AI used?** It generated code and documentation with test and layout checks. Human understanding, review and approval remain the team's responsibility. See AI_PROVENANCE.md.
