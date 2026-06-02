# Clinic Manager

Optical clinic management desktop application built with Django and Electron.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.2, Python 3.12, SQLite |
| Frontend | HTMX, Alpine.js, Tailwind CSS |
| Desktop | Electron 35 |
| Packaging | PyInstaller + electron-builder |

## Features

- **Patient management** — register, edit, search, and filter patients
- **Prescription tracking** — OD/OS fields, lens type assignment, automatic history snapshots
- **Status workflow** — Consultation → Fitting → In Production → Ready → Completed
- **Dashboard** — statistics cards, recent patients, inline status updates
- **Staff management** — role-based access (Admin, Optometrist, Staff)
- **Lens types** — configurable lens catalog
- **Backup & Restore** — download/upload SQLite database with safety checks
- **Desktop app** — loading screen, auto-migration on launch, orphan process cleanup

## Quickstart (Development)

```bash
python -m venv env
source env/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

Open http://127.0.0.1:8000 in a browser.

## Desktop Mode

```bash
npm install
npm start
```

## Build for Distribution

```bash
pyinstaller pyinstaller.spec
npm run build
```

Produces `release/Clinic Manager Setup.exe` (Windows NSIS installer).

## Models

- **Patient** — personal info, prescription, lens type, status, timestamps
- **PrescriptionRecord** — prescription change history
- **LensType** — configurable lens options
- **UserProfile** — role assignment (admin, optometrist, staff)
- **ClinicSetting** — singleton for clinic name

## Sidebar Access

| Role | Visible Sections |
|---|---|
| Admin | All sections |
| Optometrist | Dashboard, Patients, Lens Types |
| Staff | Dashboard, Patients |

## Data Directory

- **Development**: project root (`db.sqlite3`)
- **Frozen build**: `~/.clinic-manager/`
