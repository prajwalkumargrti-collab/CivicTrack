# CivicTrack — Build for Bharat | Track 5

**A full-stack, responsive civic issue reporting and resolution-tracking prototype.** Built for the Build for Bharat hackathon's Track 5: Smarter Cities and Civic Infrastructure.

> CivicTrack is an independent hackathon prototype, not an official municipal service. Reports are stored locally in the app database; they are not transmitted to BBMP or another government authority.

## 1. What problem does it address?

The selected problem statement in the supplied hackathon PDF is **“Real-Time Civic Issue Reporting & Resolution Tracking.”** The PDF identifies urban residents, local civic bodies and municipal ward officers as affected users, and calls for geotagged reporting, duplicate grouping, severity prioritisation using community verification and public resolution tracking.

CivicTrack focuses on the resident-to-officer reporting gap: citizens can submit a location-aware report with a photo and severity; similar nearby reports are flagged for review; residents can add a community confirmation; and an officer can update the status with a visible activity timeline.

## 2. Features implemented

### Citizen portal
- Responsive public landing page and civic issue categories.
- Complaint form with category, detailed description, severity, ward/area, address, photo evidence and optional coordinates.
- Leaflet map: click to pin the issue or use browser geolocation (permission required).
- Image validation and re-encoding to JPEG; 5 MB upload limit.
- Unique tracking code after submission.
- Tracking lookup requires the tracking code and last four phone digits.
- Public complaint detail, activity timeline and community confirmation.

### Officer workspace
- Password-protected officer login (Flask-Login; hashed passwords).
- KPI cards: total, active, resolved and high-priority complaints.
- Category and status charts (Chart.js).
- Map of geotagged reports.
- Search/filter complaint queue.
- Status updates with officer notes and event history.
- CSV export.

### Technical intelligence
- Possible duplicate detection: same category, within 500 metres, and TF-IDF/cosine text similarity threshold of 0.34. A match is a **review flag**, not an automatic rejection or merge.
- Explainable priority score: category baseline + citizen-selected severity + urgency terms + community confirmations. Score is capped at 100 and mapped to Low/Medium/High/Critical.
- Haversine distance calculation.

### Phase 2 — Advanced Civic Intelligence Dashboard
The officer dashboard now includes a 14-day complaint trend, ward/area-wise totals and open/resolved counts, open-complaint ageing buckets (0–2, 3–7, 8–15 and over 15 days), and average resolution time based on the first recorded Resolved event. These metrics are computed from the local database; no sample figures are hard-coded. Ward analytics depend on the ward/area entered by citizens, so inconsistent or blank ward names can appear as separate/unspecified entries. The average resolution time is a prototype operational metric and should be interpreted cautiously for records that pre-date event history.

## 3. Technology stack

- Python 3.10+
- Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF (CSRF protection)
- SQLite (local development database)
- Scikit-learn (TF-IDF and cosine similarity)
- Pillow (image validation and safe re-encoding)
- HTML, CSS, JavaScript, Leaflet/OpenStreetMap, Chart.js

The maps, Google Fonts, and Chart.js are loaded from CDNs and therefore need an internet connection. The core complaint workflow and database run locally.

## 4. Run in VS Code (Windows)

1. Install Python 3.10 or newer and VS Code.
2. Extract the ZIP file.
3. Open the extracted `CivicTrack` folder in VS Code.
4. Open Terminal → New Terminal.
5. Create and activate a virtual environment:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

```bat
.venv\Scripts\activate.bat
```

6. Install dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

7. Create your environment file:

```powershell
Copy-Item .env.example .env
```

8. Run the application:

```powershell
python app.py
```

9. Open **http://127.0.0.1:5000** in your browser.

You can also double-click `run_windows.bat`; it creates the virtual environment, installs dependencies, copies the example environment file if needed and starts the app.

## 5. Local demo officer login

- URL: `http://127.0.0.1:5000/admin/login`
- Email: `admin@civictrack.local`
- Password: `ChangeMe123!`

These are local demonstration credentials. Change `ADMIN_EMAIL` and `ADMIN_PASSWORD` in `.env` before sharing the app. Also replace `SECRET_KEY` with a long random value. For a public deployment, use HTTPS, a production WSGI server, a managed database, real identity verification, rate limiting and a reviewed privacy policy. Do not use the demo credentials in production.

## 6. Add realistic demo records

To populate the dashboard and map with clearly labelled sample data:

```powershell
python seed_demo.py
```

The script is safe to run repeatedly; it will not duplicate the fixed demo tracking IDs. Demo records are marked `[DEMO DATA]` and are not real complaints or verified municipal actions.

Demo tracking examples (phone suffix):

| Tracking code | Last 4 digits |
|---|---:|
| CT-DEMO1001 | 4821 |
| CT-DEMO1002 | 1934 |
| CT-DEMO1003 | 6720 |
| CT-DEMO1004 | 8456 |
| CT-DEMO1005 | 2309 |
| CT-DEMO1006 | 1128 |

## 7. Run tests

```powershell
pytest -q
```

The included tests cover homepage availability, geographic distance and priority-score behaviour. They are starter tests, not a full security or acceptance test suite.

## 8. Project structure

```text
CivicTrack/
├── app.py
├── seed_demo.py
├── requirements.txt
├── .env.example
├── .gitignore
├── run_windows.bat
├── run_mac_linux.sh
├── README.md
├── problem_brief.md
├── instance/              # SQLite database created at runtime
├── uploads/               # Validated uploaded evidence images
├── static/
│   ├── css/style.css
│   └── js/app.js
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── report.html
│   ├── report_success.html
│   ├── track.html
│   ├── complaint.html
│   └── admin/
│       ├── base_admin.html
│       ├── login.html
│       ├── dashboard.html
│       └── complaints.html
└── tests/test_app.py
```

## 9. Known prototype limitations — disclose these in the demo

- No integration with BBMP, municipal APIs, ward offices, SMS or email gateways. Officer status changes are simulated inside this application.
- Phone suffix and community confirmation are demo safeguards, not OTP-backed identity verification. A real rollout needs consent, secure verification and abuse prevention.
- Duplicate detection is a heuristic NLP + distance pipeline. The 0.34 similarity threshold and 500 m radius need evaluation on a labelled local dataset. It does not semantically understand every regional-language report.
- Priority scoring is explainable rule-based decision support, not a trained model, official emergency classification or automatic dispatch system. Officers retain decision authority.
- Map tiles and third-party chart/font assets require internet access. Location capture is optional and browser permission-dependent.
- SQLite and local uploads are appropriate for a single-machine demo, not a multi-ward production deployment.
- The sample dataset is synthetic and explicitly labelled.

## 10. Build for Bharat alignment checklist

| PDF requirement | CivicTrack response | Evidence in demo |
|---|---|---|
| Working application, not slides | Flask application with database-backed citizen and officer workflows | Submit a report, track it, update status |
| One problem in one track | Track 5 — Real-Time Civic Issue Reporting & Resolution Tracking | Problem brief and app workflows |
| Specific users | Urban residents, local civic bodies, municipal ward officers | Citizen portal and officer workspace |
| Geotagged reporting | Optional browser location and clickable map pin | Submit a map-pinned issue |
| Group duplicate complaints | Same-category, nearby text-similarity flag | Submit a similar issue nearby |
| Severity + community verification | Explainable priority score uses severity and confirmations | Confirm a report and inspect score |
| Public resolution tracking | Tracking code, timeline and status display | Resident tracking page |
| Demo value in a short story | Report → duplicate flag → community confirm → officer update → resolution | Use seeded demo case CT-DEMO1001 |
| Bharat-oriented UX | Responsive layout, optional location, simple language, low-dependency server-rendered pages | Test on a phone-sized browser |
| Submission artefacts | Problem brief and documented source included; demo video and GitHub publication remain team actions | `problem_brief.md`, README, repository |

This checklist maps the application to the supplied PDF; it does not guarantee selection or acceptance. Validate all workflows on the actual hackathon judging environment.

## 11. Bharat-ready experience (added)
- Public navigation, homepage, report form and tracking form support English, Kannada and Hindi interface labels. The selected language is remembered in the browser.
- Voice-assisted complaint description uses the browser Web Speech API with `en-IN`, `kn-IN` and `hi-IN` language settings where supported. Microphone audio is processed by the browser speech feature and is not uploaded by CivicTrack. Browser support and language availability vary; typing remains available.
- Complaint form drafts (category, description, severity, ward, address and optional coordinates) are saved in the browser's local storage and restored if the page is reopened. Name and mobile number are deliberately excluded from local draft storage. The draft is removed after the success page is reached.
- A service worker caches only same-origin static CSS/JavaScript/manifest assets. It deliberately does not cache authenticated pages, complaint pages, CSRF tokens or form submissions.
- The form remains usable without map tiles by entering the address and coordinates manually. Map tiles, Google/other hosted speech services used by the browser, and server submission still require connectivity.

## 12. Remaining validation for a Bharat-ready pilot
- Kannada and Hindi wording needs review by fluent speakers and testing with intended residents.
- Test voice input on the actual judging phones and browsers; provide typing as the universal fallback.
- Test offline draft recovery by opening the report form, entering non-sensitive draft details, disconnecting the network, refreshing only if the page is still served from cache, and reconnecting. This is draft assistance, not offline complaint submission.
- Measure mobile load time on a low-end Android phone and slow network. External Leaflet tiles and chart/font CDNs may still be unavailable on weak connections.
