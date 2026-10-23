# FixTrack proposal summary

FixTrack helps students and staff report campus maintenance issues and see what happens next. The goal is to make the owner, status, and final resolution of each request clear.

Email and spreadsheets can record problems, but the proposed value here is a focused workflow: a requester submits, an administrator assigns, and a worker records progress and repair notes. This is a deliberately small campus prototype, not a claim that maintenance-management systems are new.

## Initial scope

The first version supports three roles, a report form, scoped dashboards, assignment, priority, a four-state workflow, and request history. It uses sample accounts and fictional campus data. Photos, email notifications, university SSO, integrations, and emergency handling are excluded.

## Approach

Django handles templates, sessions, validation, role checks, and workflow services. SQLite stores users, requests, and change history. HTML and local CSS provide a responsive interface. The earlier proposal considered Bootstrap; this prototype uses local CSS instead to avoid CDN/network dependencies in class. This is an implementation choice for team review.

## Main delivery risk

Different screens could apply inconsistent permission or status rules. The mitigation is one backend service for state changes, a clear role matrix, and direct tests that bypass the UI. Build the whole submit-to-resolve path before adding optional features.

## Success for the review

Show one issue moving through the complete workflow and show that an unrelated user cannot access it. Present the SRS and initial architecture, identify pending quality targets, and collect feedback for SRS V2.0.

Prepared from the Group G4 project context and the October 17 SRS draft. This summary is not a record of instructor approval or a replacement for the team's submitted proposal.
