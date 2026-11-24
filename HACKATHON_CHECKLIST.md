# Build for Bharat — CivicTrack submission and validation checklist

This checklist follows the supplied Build for Bharat PDF. It is a preparation aid, not a claim of acceptance or selection.

## Required submission items

- [x] Problem brief: `problem_brief.md` (review and update after real user feedback)
- [x] Documented source repository structure: `README.md`
- [ ] Publish a clean GitHub repository (remove `.env`, databases, uploads containing personal data, virtual environments and secrets)
- [ ] Record a demo video showing a complete workflow: `DEMO_SCRIPT.md`
- [ ] Prepare the live demo environment and test credentials
- [ ] Prepare a concise explanation of value and a realistic adoption path

## Product requirements from the PDF

- [x] One clearly defined problem in one track: Track 5 — Real-Time Civic Issue Reporting & Resolution Tracking
- [x] Identify intended users: urban residents, local civic bodies and municipal ward officers
- [x] Working application rather than presentation-only screens
- [x] Geotagged complaint capture (optional browser GPS/map pin, manual address/coordinates fallback)
- [x] Potential duplicate complaint grouping/flagging
- [x] Severity and community-verification-based prioritisation
- [x] Public complaint resolution tracking
- [x] English, Kannada and Hindi interface support in the public entry flow
- [x] Voice-assisted description where browser support is available
- [x] Local draft recovery and static asset caching; this is not offline complaint submission
- [ ] Test on a low-end Android phone and slow network
- [ ] Have Kannada and Hindi translations reviewed by fluent speakers
- [ ] Test voice recognition on the exact demo browser/device
- [ ] Validate duplicate detection with labelled positive and negative examples
- [ ] Conduct resident/ward-officer feedback sessions; do not claim field validation until completed

## Final quality checks

- [ ] Citizen can submit a complaint and receive a tracking reference
- [ ] Citizen can retrieve the report using tracking reference and phone suffix
- [ ] Duplicate candidate appears only when thresholds are met and remains reviewable
- [ ] Community confirmation prevents repeat confirmation using the same demo mobile hash
- [ ] Officer can search/filter and update a complaint with a note
- [ ] Public timeline shows officer updates
- [ ] CSV export works
- [ ] Invalid coordinates, unsupported files, oversized files and missing required fields are handled
- [ ] CSRF protection and officer authentication are enabled
- [ ] Demo data is labelled synthetic
- [ ] No real citizen data or secrets are committed to GitHub

## Judging criteria in the PDF

- Problem Understanding — 25%
- Working Solution — 25%
- Innovation — 20%
- Value and Impact — 20%
- User Experience — 10%
