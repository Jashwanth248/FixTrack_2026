# FixTrack SRS V1.0

> Imported from the October 17 proposed SRS draft. The prototype status is tracked separately in TRACEABILITY.md. Team approval is still to be recorded.

## FixTrack Software Requirements Specification

Campus Maintenance Request System
Version 1.0 • Group G4 • October 17, 2026

Document status: Proposed baseline for team review. Requirements below are implementation targets, not claims that features have been built or tests have passed. Team approval is pending.

## 1 Introduction

### 1.1 Purpose

FixTrack will help students and staff report campus maintenance problems and follow their progress. This specification defines what the prototype must do, who may perform each action, and how the team will check the result. It is intended for our development team, instructor, and anyone implementing or testing the system, including an AI coding agent.

### 1.2 Scope

Version 1 includes sign-in with sample accounts, maintenance request submission, role-based dashboards, worker assignment, priority changes, status updates, resolution notes, filters, and a timestamped history. The prototype uses fictional campus data. It is not an emergency reporting service.

Out of scope: public registration, password reset, university single sign-on, photos or other attachments, email or SMS notifications, live university integrations, request deletion, reopening resolved requests, and production deployment. No special hardware is required.

### 1.3 Team roles

| Member | Roles and responsibility |
| --- | --- |
| Shiva Keerthi Putluri | Project Manager / Leader; UI/UX Designer; Software Engineer / Programmer. Coordinates scope and review; designs and builds the interface. |
| Jashwanth Bheema | Assistant Project Manager; Software Engineer / Programmer. Defines backend behavior, database relationships, permissions, and integration. |
| Meghdeep Jana | Quality Assurance & Documentation; Software Engineer / Programmer. Maintains tests and requirements records; supports history and reporting features. |

### 1.4 Document organization

Section 2 describes users, scope rules, and interfaces. Section 3 specifies EARS requirements, data, and measurable quality targets. Section 4 defines verification and misuse tests. Appendices record AI assistance, traceability, terms, and revisions. Structure follows the supplied course Trailhead example.

## 2 Overall description

### 2.1 Product perspective and approach

FixTrack is a self-contained browser application. Proposed implementation: Django and Django templates, HTML, CSS, Bootstrap, and SQLite. The browser sends requests to Django; Django authenticates the user, checks permissions, validates the operation, and commits changes to SQLite. The browser never connects directly to the database. Version 1 has no external service dependency. Package versions will be pinned when implementation begins.

### 2.2 Users and access boundaries

| Action | Requester | Administrator | Worker |
| --- | --- | --- | --- |
| Create a request | Yes | No | No |
| View requests and history | Own only | All | Currently assigned only |
| Set priority or assign worker | No | Unresolved only | No |
| Start or resolve work | No | No | Currently assigned only |
| Edit original report or delete | No | No | No |

Each account has exactly one role. A requester represents a student or staff member. Seeded accounts are created by a developer setup command; there is no account-management UI. At least two requester accounts and two worker accounts are needed for access-control tests.

### 2.3 Workflow rules

| Current state | Allowed action and actor | Result |
| --- | --- | --- |
| Submitted | Administrator assigns an active worker | Assigned |
| Assigned | Administrator changes worker | Assigned |
| Assigned | Assigned worker starts work | In Progress |
| In Progress | Administrator changes worker | In Progress |
| In Progress | Assigned worker supplies resolution note | Resolved |
| Resolved | Read only | No further changes |

Priority is Low, Medium, or High; new requests default to Medium. An administrator may change priority in any unresolved state. Assignment never clears a worker or moves work backward. A worker replaced by reassignment immediately loses access. No other status transition is allowed. Status is changed by named actions, not an editable free-text field.

### 2.4 Constraints and dependencies

The baseline targets a single-campus classroom prototype, online browser use, and one application instance. SQLite limits make this a small-demo design, not a production scale commitment. The team will prioritize the complete submit-to-resolve workflow before visual refinements. The main risk is inconsistent permission and state rules; centralized backend checks and direct denied-operation tests mitigate it.

Assumptions: users can use a standard web form; sample accounts and fictional locations are available; the demo machine has Python and the pinned dependencies. Any network-accessible demonstration requires HTTPS. Local-only development may use HTTP on localhost.

## 3 Specific requirements

### 3.1 Functional requirements in EARS

All FR requirements are Must for version 1.0. “When” identifies a trigger, “While” identifies a state, and “If … then” identifies unwanted behavior. Terms and validation rules in Sections 2 and 3.4 are normative.

### FR-01

When a user submits valid credentials for an active sample account, FixTrack shall establish an authenticated session and display that account’s role-specific dashboard.

### FR-02

If credentials are invalid or the account is inactive, then FixTrack shall deny sign-in and display “Invalid username or password” without identifying which field failed.

### FR-03

While a user is unauthenticated, FixTrack shall redirect protected-page requests to sign-in without returning maintenance data or changing records.

### FR-04

When an authenticated user signs out, FixTrack shall invalidate the server-side session and return the user to sign-in.

### FR-05

While a requester is authenticated, when they submit valid location, category, and description fields, FixTrack shall create one request with a unique ID, the session user as owner, status Submitted, priority Medium, no worker, and server-generated creation and update times.

### FR-06

If any submitted field violates Section 3.4, then FixTrack shall reject the complete operation, preserve entered form values, show a field-specific error, and leave stored data unchanged.

### FR-07

When an authenticated user opens the dashboard, FixTrack shall list only the requests permitted by Section 2.2, showing ID, location, category, priority, status, and last update time, ordered by last update descending and then ID descending.

### FR-08

When an authorized user opens a request, FixTrack shall display its original report, owner display name, assigned worker display name or “Unassigned,” priority, status, resolution note if present, and complete recorded history.

### FR-09

When a user applies status, category, or priority filters, FixTrack shall return only permitted requests matching all selected filters; when no request matches, it shall display “No matching requests.”

## 3.1 Functional requirements continued

### FR-10

While a request is unresolved, when an administrator selects an active worker, FixTrack shall assign that worker and apply the assignment state rule in Section 2.3.

### FR-11

While a request is unresolved, when an administrator selects Low, Medium, or High priority, FixTrack shall store that priority without changing status or assignment.

### FR-12

While a request is Assigned, when its currently assigned worker selects Start work, FixTrack shall change its status to In Progress.

### FR-13

While a request is In Progress, when its currently assigned worker submits a valid resolution note, FixTrack shall store the note, set status to Resolved, and record the server resolution time.

### FR-14

If an authenticated user requests an operation outside their role or record permissions, then FixTrack shall return HTTP 403 with no record content and make no change; for a nonexistent ID, it shall return HTTP 404.

### FR-15

If an authorized operation would violate the workflow rules, then FixTrack shall return HTTP 409, display “This action is not allowed in the current status,” and leave the request unchanged.

### FR-16

When a creation, assignment, priority, or status change succeeds, FixTrack shall append a history entry recording the request ID, actor ID, action, server timestamp, and old and new values of changed tracked fields within the same database transaction.

### FR-17

If the submitted version of a request differs from its stored version, then FixTrack shall reject the update with HTTP 409 and instruct the user to reload; when an update succeeds, it shall increase the version by one.

### FR-18

If persistence fails during a create or update operation, then FixTrack shall roll back the request and its history changes together and display “Unable to save. Please try again” without exposing internal error details.

Additional operation rules: permissions are checked before validation or state changes. Requests use GET for reads and POST for writes. A no-change assignment or priority submission returns success without a new history entry or version increment. New records begin at version 1. History is ordered by timestamp ascending, then history ID ascending. The version check and write must be atomic.

## 3.2 Interfaces and data requirements

### 3.2 External interfaces

The interface contains a sign-in page, role-specific dashboard, requester submission form, and request detail page. Requesters see their own reports; administrators see assignment and priority controls; workers see Start work or Resolve only when the current state allows it. Hidden controls are a usability aid; the server enforces every rule independently.

The dashboard shows 20 rows per page and Previous and Next controls. Filters apply before pagination. Clearing filters restores all permitted requests. A new filter selection returns to page 1. Every field has a visible label; errors appear next to the affected field and in a summary. A persistent notice states that emergencies must use campus emergency channels.

Browser and server communicate using HTML forms and HTTPS outside localhost. There is no public API requirement. All data operations use Django database access. No device sensors, special hardware, file uploads, or external notifications are required.

### 3.4 Data requirements and validation

| Entity or field | Required rule |
| --- | --- |
| User | Unique ID and username; display name; salted password hash; active flag; exactly one role: Requester, Administrator, Worker. Roles are not accepted from browser form values. |
| Request identity | Unique integer ID; immutable owner and original report; foreign keys to owner and nullable assigned worker. |
| Location | Required plain text, 3–100 characters after trimming. Fictional building and room or area, such as “Library Room 204.” |
| Category | Exactly one of Electrical, Plumbing, Furniture, HVAC, or Other. |
| Description | Required plain text, 10–1000 characters after trimming. |
| Resolution note | Required only for resolution; 10–1000 characters after trimming; plain text. No separate comment feature. |
| State and priority | Enumerations in Section 2.3 only. Submitted has no worker; later states require a worker. Resolved requires a note and resolution time. |
| Times and version | UTC server timestamps for created, updated, resolved, and history; show UTC explicitly in the UI. Positive integer version for concurrent updates. |
| History | Unique ID, request foreign key, actor foreign key, action, time, old/new status, priority, and worker where changed. Creation records initial values. |

Reject empty, out-of-range, or unsupported values server-side, even when browser validation is bypassed. State, owner, timestamps, and role are never taken from client-supplied values. Reject unexpected writable fields with HTTP 400. Requester and worker accounts cannot modify request history. No application role can edit or delete recorded history.

Committed data must survive application restart. Demo records remain until the team deliberately resets the fictional dataset outside the application. A reset is not a user feature and must not run during verification. No real student records, secrets, or medical or emergency details should be entered.

## 3.3 Non functional requirements

These targets apply to the defined prototype and require evidence before being marked passed. Security requirements apply on every route, including direct requests that bypass the interface.

NFR-01 — Performance. With 1,000 seeded requests and 10 concurrent authenticated clients, 95% of dashboard and detail responses shall complete within 2 seconds during a 5-minute test on a documented machine with at least 2 CPU cores and 4 GB RAM. Record hardware and tool settings.

NFR-02 — Passwords. All account passwords shall use Django’s configured salted PBKDF2 password hasher. No plaintext password shall appear in database fields, application logs, or committed files. Review settings and all seeded account records.

NFR-03 — Transport and sessions. Network-accessible demos shall use HTTPS with TLS 1.2 or higher and Secure, HttpOnly, SameSite=Lax session cookies. Sessions shall expire after 30 minutes of inactivity. Logout and expired sessions shall fail all protected access checks.

NFR-04 — Login abuse. For each username and each source IP, the sixth login attempt after five failures in a rolling 10-minute window shall be blocked with HTTP 429 until that counter falls below five. Apply username counters to unknown names too; show the same error behavior. Counters persist across application restart.

NFR-05 — Authorization. 100% of role and ownership cases in the Section 2.2 matrix shall pass direct server tests. Each permitted route shall also be tested with the wrong role, another owner or worker, and no session.

NFR-06 — Input and request safety. All state-changing requests shall require a valid CSRF token. All displayed user text shall be HTML-escaped. Database operations shall use parameterized ORM queries. Missing-token and script/injection tests shall cause no unauthorized change or script execution.

NFR-07 — Data integrity. A forced persistence failure shall leave zero partial request/history changes. Two updates with the same original version shall result in exactly one commit and one conflict. All committed data shall remain identical after a normal restart.

NFR-08 — Usability. At least four of five first-time test participants shall sign in and submit a valid fictional request within 3 minutes, using only on-screen labels and instructions. Record task time and success; do not claim a test before it occurs.

NFR-09 — Compatibility and access. Core workflow shall work at 390×844 and 1366×768 viewports in the Chrome and Firefox versions recorded at test time, with no horizontal page scroll. All actions shall be keyboard-operable with visible focus, labeled inputs, and errors stated in text.

NFR-10 — Maintainability. Automated tests shall cover every FR and all state transitions. Coverage shall reach at least 80% of statements in permission, validation, and transition modules. The chosen linter shall report zero errors; dependencies shall be pinned.

NFR-11 — Recovery. With application writes stopped, a documented database backup and restore procedure shall restore a 1,000-request dataset in 10 minutes or less. Verify request/history counts and record equality against the backup.

NFR-12 — Secrets and errors. No database file, credentials, session token, or secret key shall be committed to the repository. Non-local demos shall disable debug mode. Forced error responses shall contain no stack trace or secret; logs shall exclude passwords, tokens, and request descriptions.

## 4 Verification and misuse cases

### 4.1 Acceptance approach

All tests below are planned. Meghdeep maintains test evidence; Jashwanth reviews backend results; Keerthi coordinates scope and final review. Passing means all Must FR tests and all NFR targets meet the specified outcomes. A failed security or integrity test blocks acceptance. Any unmet target requires a documented baseline change, not an undocumented exception.

For TC-01 through TC-18, the expected result is the corresponding FR statement. Include valid, invalid, and boundary inputs where applicable. TC-06 checks trimmed lengths at minimum minus one, minimum, maximum, and maximum plus one; TC-09 checks combined filters, empty results, and pagination; TC-10 through TC-15 cover every allowed and forbidden transition.

Test data: requester A and B, administrator A, worker A and B, and an inactive account. Seed requests in every state, with known owners, workers, and versions. Store test IDs, input, expected result, actual result, pass/fail, execution date, and code revision. Capture status codes and database before/after values for denied actions.

### 4.2 Foreseeable abuse and misuse

| Case | Attempt and expected protection | Evidence |
| --- | --- | --- |
| AC-01 Other user data | Requester A changes a URL to requester B’s ID. FR-14 denies content and mutation. List filters never expand access. | TC-07, TC-14; NFR-05 |
| AC-02 Role escalation | Worker posts an administrator assignment action or changes owner/role fields. Server rejects the operation or unexpected field. | TC-06, TC-14; NFR-05 |
| AC-03 Workflow bypass | Worker resolves Submitted directly, repeats resolution, or edits a resolved request. No changes are stored. | TC-15; NFR-07 |
| AC-04 Stale update | Two workers/admin sessions submit the same version, or a replaced worker submits an old form. At most one valid update commits; removed access is denied. | TC-14, TC-17; NFR-07 |
| AC-05 Password guessing | Repeated failed logins reach the username or IP threshold. Subsequent attempt is throttled. | Security test ST-04 |
| AC-06 Script or injection | A description contains script markup or SQL-like text. Text remains inert and database structure/data outside the request stays unchanged. | ST-06 |
| AC-07 Forged form | A write is posted with a missing/invalid CSRF token. The server rejects it with no change. | ST-06 |
| AC-08 Log tampering | A client attempts to update or delete a history record. There is no permitted application operation; direct requests are denied. | TC-14, TC-16 |

### 4.3 Demonstration scenario

Requester A reports a broken projector in Library Room 204 under Electrical. The administrator assigns worker A and High priority. Worker A starts the task and resolves it with a repair note. Requester A sees all recorded changes. Requester B and worker B are denied direct access. A repeated resolution causes no second update.

## Appendix A AI assistance and provenance

| Item | Record for this version |
| --- | --- |
| Tool | OpenAI ChatGPT, used October 17, 2026. The exact model/version was not independently recorded. |
| Inputs supplied | FixTrack project context and team roles; assignment instructions; uploaded course Trailhead SRS example and CHD sample. |
| AI contribution | ChatGPT drafted and organized this SRS, proposed EARS wording, measurable quality targets, permissions, state rules, verification cases, and traceability. It also generated the document formatting. |
| Human supplied material | The project idea, proposal scope, team identities/roles, course instructions, and reference templates came from the user/course material. Do not describe all detailed requirements as human-authored. |
| Prompt summary | Prepare FixTrack SRS V1.0 using the uploaded EARS example; include functional and measurable non-functional/security requirements, misuse cases, traceability, team roles, and AI provenance. This is a summary, not a verbatim prompt log. |
| Review performed by assistant | Aligned the draft to the supplied template; checked role/state consistency, requirement-to-test mapping, scope exclusions, and document layout. These checks are not team approval or software testing. |
| Human review still required | Team members must review every requirement, confirm proposed limits and workflow choices, revise wording they cannot defend, and record approval. No stakeholder interview, implementation, security audit, or executed test is claimed. |
| AI implementation controls | Before coding, a human approves the relevant spec, plan, and task list. Generated changes undergo code review and independent tests. Record tool/date, requirement IDs, prompts, code revision, reviewer, corrections, and test evidence for each future use. |

### Proposed decisions requiring team review

Confirm: only the assigned worker may resolve; resolved requests cannot reopen; priority defaults to Medium; no original-report editing; 20-row pages; field lengths; five-failure login threshold; 30-minute idle timeout; performance and usability targets. These are concrete proposed choices so implementation has one meaning, not verified customer demands.

### References

Group G4. (2026). Campus maintenance request system [Project proposal]. MSCS 2101, Sofia University.

Sofia University. (n.d.). SRS example Trailhead [Course-provided worked example]. MSCS 2101. Used for IEEE-style organization, EARS patterns, measurable NFRs, provenance, and traceability.

Sofia University. (n.d.). SRS CHD V1.0 [Course-provided sample; internal title identifies version 2.1, 2018]. Used as a secondary example of interfaces and verification sections.

OpenAI. (2026). ChatGPT [Large language model]. https://chatgpt.com/

## Appendix B Traceability matrix

Origins: P1 = reporting and tracking; P2 = assignment and workflow; P3 = permissions and integrity, all from the project proposal. Q = AI-assisted proposed measurable quality target. Components and tests are planned, not built. Every requirement below is pending verification.

| Requirement | Origin | Planned design element | Planned verification |
| --- | --- | --- | --- |
| FR-01 | P3 | Authentication | TC-01 |
| FR-02 | P3 | Authentication | TC-02 |
| FR-03 | P3 | Access middleware | TC-03 |
| FR-04 | P3 | Authentication | TC-04 |
| FR-05 | P1 | Request service | TC-05 |
| FR-06 | P1 | Validation | TC-06 |
| FR-07 | P1/P3 | Dashboard query | TC-07 |
| FR-08 | P1 | Detail view | TC-08 |
| FR-09 | P1 | Dashboard query | TC-09 |
| FR-10 | P2 | Assignment service | TC-10 |
| FR-11 | P2 | Priority service | TC-11 |
| FR-12 | P2 | Transition service | TC-12 |
| FR-13 | P2 | Transition service | TC-13 |
| FR-14 | P3 | Permission service | TC-14 |
| FR-15 | P2 | Transition service | TC-15 |
| FR-16 | P1/P3 | History transaction | TC-16 |
| FR-17 | P3 | Version guard | TC-17 |
| FR-18 | P3 | Transaction handler | TC-18 |
| NFR-01 | Q | Load harness | LT-01: response percentile |
| NFR-02 | Q/P3 | Password settings | ST-02: hashes and log review |
| NFR-03 | Q/P3 | Session and TLS settings | ST-03: cookies, idle, TLS |
| NFR-04 | Q/P3 | Persistent rate limiter | ST-04: thresholds and restart |
| NFR-05 | Q/P3 | Permission service | ST-05: full access matrix |
| NFR-06 | Q/P3 | CSRF, templates, ORM | ST-06: forged/script/injection |
| NFR-07 | Q/P3 | Database transactions | IT-07: fault, concurrency, restart |
| NFR-08 | Q | Forms and labels | UT-08: five timed participants |
| NFR-09 | Q | Responsive templates | UI-09: browsers, sizes, keyboard |
| NFR-10 | Q | Tests and lint config | QA-10: trace, coverage, lint |
| NFR-11 | Q | Backup procedure | RT-11: timed restore and compare |
| NFR-12 | Q/P3 | Configuration and logging | ST-12: secrets and errors |

## Appendix C Glossary and change control

| Term | Meaning |
| --- | --- |
| EARS | Easy Approach to Requirements Syntax; structured trigger/state/response wording. |
| SRS | Software Requirements Specification; the agreed expected system behavior. |
| FR and NFR | Functional Requirement and Non-Functional Requirement. |
| Requester | Student or staff sample account that creates and tracks its own reports. |
| Administrator | Application role that sees all requests and manages assignment and priority. |
| Worker | Maintenance sample account that works on currently assigned requests. |
| CSRF | Cross-site request forgery; a forged request made using another user’s session. |
| ORM | Object-relational mapper; Django’s mechanism for database operations. |
| UTC | Coordinated Universal Time; timestamp standard used for this prototype. |
| Atomic transaction | A set of database changes that all commit or all roll back. |
| Optimistic concurrency | Rejecting a stale update by comparing submitted and stored version numbers. |
| SDD and STP | Software Design Description and Software Test Plan; future detailed design and test artifacts. |

### Revision history

| Version | Date | Prepared for | Change |
| --- | --- | --- | --- |
| 1.0 | October 17, 2026 | Group G4 | Initial AI-assisted proposed requirements baseline using the course EARS template. Team review pending. |

### Review ownership

Keerthi reviews scope and interface behavior. Jashwanth reviews data rules, permissions, and feasibility. Meghdeep reviews measurability, traceability, misuse cases, and test coverage. Approval date and reviewer sign-off must be recorded after actual review; none is asserted in this draft.

### Changes after the Module 4 pitch

For each change, record the affected requirement ID, reason, source of feedback, effect on design and tests, owner, and approval date. Preserve existing IDs; assign new IDs to additions and mark removed requirements as retired. Incorporate accepted pitch feedback into SRS V2.0 for Module 5. Update traceability and AI provenance whenever requirements change.
