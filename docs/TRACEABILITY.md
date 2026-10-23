# SRS implementation status at the initial review

The October 17 SRS remains a **proposed** baseline. “Implemented” below means code exists and named automated checks support it; it does not imply team sign-off or full acceptance. Test methods are in `maintenance/tests.py`.

| Requirement | Component | Automated evidence / status |
|---|---|---|
| FR-01–02 | sign_in | test_login_and_logout; test_login_invalid_and_inactive |
| FR-03 | login_required | test_anonymous_protected |
| FR-04 | sign_out | test_login_and_logout |
| FR-05 | create_ticket | test_complete_workflow; test_field_validation_and_trim |
| FR-06 | forms + unexpected-field checks | test_field_validation_and_trim; test_server_fields_rejected; test_invalid_worker |
| FR-07 | dashboard + visible_tickets | test_owner_scope_and_admin_scope; test_filters_pagination_and_empty |
| FR-08 | detail | test_review_and_forms_render; browser demo |
| FR-09 | dashboard filters | test_filters_pagination_and_empty |
| FR-10 | assignment service | test_assignment_restricts_workers; test_invalid_worker |
| FR-11 | priority service | test_priority_noop; test_stale_forms_no_lost_update |
| FR-12–13 | transition service | test_complete_workflow; test_invalid_transition_and_short_resolution |
| FR-14 | permission service | test_wrong_role_and_unknown_action; test_owner_scope_and_admin_scope; test_missing_record |
| FR-15 | state guards | test_invalid_transition_and_short_resolution; test_resolved_read_only |
| FR-16 | History transaction | test_complete_workflow; test_history_failure_rolls_back_create |
| FR-17 | version guard | test_stale_forms_no_lost_update; parallel-writer stress test pending |
| FR-18 | rollback + error views | test_history_failure_rolls_back_update |
| NFR-01 Performance | No load claim | 1,000 requests / 10-client / p95 test pending |
| NFR-02 Passwords | Django salted password hashing | Configuration present; full repository/database/log inspection pending team review |
| NFR-03 Transport/session | Idle middleware + secure mode settings | test_idle_timeout; HTTPS infrastructure not deployed or verified |
| NFR-04 Login abuse | LoginAttempt records | test_login_throttle_by_username_and_ip; persistent database model; restart measurement pending |
| NFR-05 Authorization | Server checks | Negative role/owner/worker checks executed; full route matrix sign-off pending |
| NFR-06 Input security | CSRF, escaped templates, ORM | test_csrf; test_html_escaped; explicit injection test pending |
| NFR-07 Integrity | Atomic changes, version guard | Rollback and stale-form tests; restart equality measurement pending |
| NFR-08 Usability | Labeled forms | Five-person timed test pending |
| NFR-09 Compatibility | Responsive local CSS | Chromium desktop/mobile smoke check; Firefox and full keyboard review pending |
| NFR-10 Maintainability | Test suite + CI | Requirement mapping present; lint and 80% core coverage gate pending |
| NFR-11 Recovery | No automated backup feature | Timed backup/restore validation pending |
| NFR-12 Secrets/errors | Environment config + generic errors | No runtime secrets/data committed; full operational logging audit pending |

## Scope choices

No changes to the required core workflow were made. Local CSS replaces the optional Bootstrap styling choice for offline presentation. All accounts are created by a local seed command; public registration and account editing remain excluded. The full SRS is in [SRS_V1.md](SRS_V1.md).
