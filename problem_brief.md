# CivicTrack — Problem Brief

## Track
**Track 5: Smarter Cities and Civic Infrastructure**

## Selected problem prompt
**Real-Time Civic Issue Reporting & Resolution Tracking** — the supplied Build for Bharat PDF describes citizens reporting urban issues such as potholes, garbage dumps and broken streetlights while municipal response remains opaque and slow.

## People affected
- Urban residents who encounter local infrastructure and sanitation issues.
- Local civic bodies that need structured, location-aware reports.
- Municipal ward officers who review, prioritise and coordinate action.

## Problem and current gap
A resident may report a pothole or overflowing garbage through a helpline, social channel or in-person visit, but the report can lack a precise location, useful evidence or a clear status reference. Similar reports may arrive separately. Residents may not know whether an issue was received, assigned or resolved. The core gap addressed here is fragmented information and weak visibility between resident reporting and officer follow-up. This is a product hypothesis to validate with local residents and ward staff; CivicTrack does not claim to have completed field research.

## Proposed solution
CivicTrack is a responsive civic reporting and resolution-tracking portal. A resident submits an issue category, description, severity, address, optional map pin and photo. The system creates a private tracking reference. A lightweight NLP and distance check flags a similar nearby report for officer review. Community members can confirm a report, and an explainable score combines category, severity, urgency terms and confirmations. Officers use a protected dashboard to review reports, filter the queue, update status and add notes. Residents can see the resulting status timeline.

## Why this is different in the prototype
- A single traceable workflow links citizen report, community confirmation, officer status update and public tracking.
- Geospatial and text similarity are combined to flag potential duplicates rather than treating every report independently.
- Duplicate flags remain reviewable; no report is automatically deleted or rejected.
- The priority score is visible and explainable rather than presented as a black-box AI decision.

## Value to demonstrate
For a judge demo, show one resident reporting a road hazard with a map pin; a second similar nearby report being flagged; a community confirmation increasing its score; an officer changing status with a note; and the resident seeing the update in the timeline. This demonstrates an end-to-end working workflow. Real response-time improvement must be measured through a pilot with residents and municipal staff; it is not claimed by this prototype.

## Adoption path
A future pilot could start with one ward and a named civic partner. Before live use, the team would need municipal workflow agreement, officer accounts, secure identity verification, consent and retention rules, language localisation, accessibility testing, notification integration, service-level reporting, and deployment on managed infrastructure. No municipal integration exists in this prototype.

## Risks and safeguards
- Community confirmations can be abused; current phone-suffix demo checks are not identity proof. Production needs OTP or verified accounts, rate limits and moderation.
- Duplicate similarity can produce false positives; all matches are flags for officer review.
- Priority scoring can encode bias; it is a transparent support signal, not a final decision or emergency triage.
- Citizen contact and location data are sensitive; production needs data minimisation, access control, retention policy and secure hosting.
- Demo data is synthetic and labelled; no synthetic record should be represented as a real municipal action.
