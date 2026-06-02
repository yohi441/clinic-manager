# Documentation — Clinic Manager

> Optical clinic management desktop application built with Django and Electron.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Directory Structure](#3-directory-structure)
4. [Backend — Django](#4-backend--django)
   - 4.1 Configuration
   - 4.2 Models
   - 4.3 Views
   - 4.4 URL Routing
   - 4.5 Forms
   - 4.6 Admin
   - 4.7 Middleware
   - 4.8 Signals
   - 4.9 Context Processors
5. [Frontend — Templates](#5-frontend--templates)
   - 5.1 Base Layout
   - 5.2 Dashboard
   - 5.3 Patient List
   - 5.4 Partials
   - 5.5 Settings Pages
   - 5.6 Login
6. [Desktop Shell — Electron](#6-desktop-shell--electron)
7. [HTMX Architecture](#7-htmx-architecture)
8. [Alpine.js Components](#8-alpinejs-components)
9. [Role-Based Access Control](#9-role-based-access-control)
10. [Prescription History](#10-prescription-history)
11. [Backup & Restore](#11-backup--restore)
12. [Build & Distribution](#12-build--distribution)
13. [Extending the App](#13-extending-the-app)

---

## 1. Project Overview

**Clinic Manager** is a self-contained desktop application for managing an optical (eye care) clinic. It handles patient records, eyeglass prescriptions, lens type catalogs, order status tracking, staff management, and database backup/restore.

| Layer | Technology |
|---|---|
| Backend | Django 5.2.14, SQLite |
| Frontend | HTMX 2.x, Alpine.js 3.x, Tailwind CSS 3.x (CDN) |
| Desktop shell | Electron 35 |
| Packaging | PyInstaller (Django → .exe) + electron-builder (NSIS installer) |
| Python deps | `Django==5.2.14`, `django-template-partials==25.3` |
| Node deps | `electron`, `electron-builder` |

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────┐
│  Electron Window (Chromium)                         │
│  ┌───────────────────────────────────────────────┐  │
│  │  Django Templates + HTMX + Alpine.js          │  │
│  │  (base.html, dashboard.html, partials, etc.)   │  │
│  └──────────────┬────────────────────────────────┘  │
│                 │ HTTP (127.0.0.1:<random-port>)     │
│  ┌──────────────▼────────────────────────────────┐  │
│  │  Django Development Server (manage.py)         │  │
│  │  or compiled backend (clinic-backend.exe)      │  │
│  │                                                │  │
│  │  conf/settings.py → core/views.py → models.py │  │
│  │                              → templates/     │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

- Electron starts, finds a free TCP port, spawns the Django backend, waits for it to respond, then loads the URL.
- In development: runs `python manage.py runserver`.
- In production: runs the PyInstaller-compiled `clinic-backend.exe`.
- All frontend assets (Tailwind, HTMX, Alpine.js, Flatpickr) are loaded from local vendor files — no internet required.

---

## 3. Directory Structure

```
prs/
├── manage.py                  # Django CLI entry point
├── main.js                    # Electron main process
├── package.json               # Node config, electron-builder settings
├── pyinstaller.spec           # PyInstaller build spec
├── requirements.txt           # Python dependencies
├── .gitignore
├── db.sqlite3                 # SQLite database (dev)
│
├── conf/                      # Django project configuration
│   ├── __init__.py
│   ├── settings.py            # ALL settings (DB, middleware, templates, static, auth)
│   ├── urls.py                # Root URL config (admin/ + core.urls)
│   ├── wsgi.py                # WSGI entry point
│   └── asgi.py                # ASGI entry point
│
├── core/                      # Django application
│   ├── __init__.py
│   ├── apps.py                # App config — imports signals on ready
│   ├── models.py              # Patient, PrescriptionRecord, LensType, UserProfile, ClinicSetting
│   ├── views.py               # All views (dashboard, CRUD, settings, backup)
│   ├── urls.py                # URL routing for core app
│   ├── forms.py               # PatientForm with Tailwind-styled widgets
│   ├── admin.py               # Django admin registration
│   ├── middleware.py          # AutoMigrateMiddleware (runs migrate on frozen start)
│   ├── signals.py             # Auto-create UserProfile on User creation
│   ├── context_processors.py  # CLINIC_NAME → every template
│   ├── tests.py               # Placeholder
│   ├── migrations/            # Database migrations (13 files)
│   └── static/
│       └── vendor/            # Bundled JS/CSS (self-contained, no CDN needed)
│           ├── js/
│           │   ├── tailwind.min.js
│           │   ├── htmx.min.js
│           │   ├── alpine.min.js
│           │   └── flatpickr.min.js
│           └── css/
│               ├── inter.css  # Inter font
│               └── flatpickr.min.css
│
├── templates/                 # Django templates
│   ├── base.html              # Root layout: sidebar, header, modal container, toast
│   ├── dashboard.html         # Dashboard with stat cards, recent patients table
│   ├── patient_list.html      # Patient list with search, filter, pagination
│   ├── page_unavailable.html  # Placeholder for future features
│   ├── registration/
│   │   └── login.html         # Login page
│   ├── partials/
│   │   ├── sidebar.html       # Navigation sidebar (role-aware)
│   │   ├── patient_table.html # Reusable patient table with pagination
│   │   ├── patient_detail.html# Patient detail modal with prescription history
│   │   └── status_badge.html  # Color-coded status badge
│   └── settings/
│       ├── staff_list.html        # Staff CRUD (admin only)
│       ├── staff_edit.html        # Edit staff modal
│       ├── lens_type_list.html    # Lens type CRUD
│       ├── lens_type_edit.html    # Edit lens type modal
│       └── backup.html            # Backup/restore UI
│
├── static/                    # Top-level static files
│   ├── icon.ico               # Windows app icon
│   ├── favicon.svg
│   └── logo.svg
│
├── staticfiles/               # Collected static files (production, `collectstatic` output)
└── env/                       # Python virtual environment (not tracked)
```

---

## 4. Backend — Django

### 4.1 Configuration (`conf/settings.py`)

**Frozen-mode detection** (line 18):
```python
_FROZEN = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
```
When the app is compiled with PyInstaller, `sys.frozen` is `True` and `sys._MEIPASS` points to the temp extraction directory. This flag is used throughout settings.

**Data directory** (lines 34–44):
- Dev: `BASE_DIR` (project root, alongside `manage.py`)
- Frozen: `~/.clinic-manager/` (overridable via `CLINIC_DATA_DIR` env var)
- On first frozen launch, the bundled `db.sqlite3` is copied to the data dir.

**Key settings**:
| Setting | Value | Notes |
|---|---|---|
| `SECRET_KEY` | Hardcoded (insecure) | For local use only. Change for any real deployment. |
| `DEBUG` | `True` | Set `False` for production. |
| `ALLOWED_HOSTS` | `['127.0.0.1', 'localhost']` | Only local access. |
| `DATABASES` | SQLite at `DATA_DIR / 'db.sqlite3'` | Single-file database. |
| `TEMPLATES` | Loader uses `template_partials` | Enables `{% partialdef %}` syntax. |
| `STATIC_ROOT` | `BASE_DIR / 'staticfiles'` | Output of `collectstatic`. |
| `LOGIN_URL` | `/accounts/login/` | All views require login. |
| `LOGIN_REDIRECT_URL` | `/` | Dashboard after login. |
| `INSTALLED_APPS` | Includes `core` app | Core app does everything. |

**Middleware order** (lines 66–75):
1. `SecurityMiddleware`
2. `AutoMigrateMiddleware` (custom — runs migrations on frozen start)
3. `SessionMiddleware`
4. `CommonMiddleware`
5. `CsrfViewMiddleware`
6. `AuthMiddleware`
7. `MessagesMiddleware`
8. `XFrameOptionsMiddleware`

**Template context processors** (lines 90–95):
- `request` (Django built-in)
- `auth` (Django built-in — provides `user` in templates)
- `messages` (Django built-in)
- `core.context_processors.clinic_settings` (provides `{{ CLINIC_NAME }}`)

### 4.2 Models (`core/models.py`)

#### `UserProfile`
- **Purpose**: Extends Django's `User` with a role field.
- **Fields**:
  - `user` — OneToOneField → User
  - `role` — CharField with choices: `admin`, `optometrist`, `staff`
- **Auto-created**: Via signal (`signals.py`) — superusers get `admin`, regular users get `staff`.

#### `LensType`
- **Purpose**: Configurable lens catalog (e.g., Transition, Polarized, Progressive).
- **Fields**:
  - `name` — CharField, unique
  - `is_active` — BooleanField (for soft disabling)
- **Ordering**: by `name`.

#### `Patient`
- **Purpose**: Core model — stores all patient information.
- **Fields**:

| Field | Type | Notes |
|---|---|---|
| `first_name` | CharField | |
| `last_name` | CharField | |
| `date_of_birth` | DateField | Nullable |
| `gender` | CharField | Male/Female |
| `contact` | CharField | Phone number |
| `prescription_od` | CharField | Right eye (free text) |
| `prescription_os` | CharField | Left eye (free text) |
| `lens_type` | ForeignKey → LensType | Nullable, SET_NULL |
| `address` | TextField | |
| `notes` | TextField | |
| `status` | CharField | Consultation / Fitting / In Production / Ready / Completed |
| `last_visit` | DateField | Defaults to today |
| `created_at` | DateTimeField | Auto on create |
| `updated_at` | DateTimeField | Auto on update |
| `updated_by` | ForeignKey → User | Nullable |

- **Property**: `age` — calculated from `date_of_birth`.

#### `PrescriptionRecord`
- **Purpose**: Audit log of prescription changes.
- **Fields**:
  - `patient` — ForeignKey → Patient
  - `prescription_od`, `prescription_os` — snapshot of prescription at time of change
  - `lens_type` — ForeignKey → LensType (snapshot)
  - `notes` — TextField
  - `updated_by` — ForeignKey → User
  - `created_at` — DateTimeField (auto)
- **Ordering**: newest first.
- **Created automatically** in `patient_form` view when prescription values change.

#### `ClinicSetting`
- **Purpose**: Singleton model for app-wide settings.
- **Fields**:
  - `clinic_name` — CharField, default `'Eye Clinic'`
- **Method**: `load()` — `get_or_create(pk=1)`, ensures only one instance.

### 4.3 Views (`core/views.py`)

All views require `@login_required`. Some additionally require specific roles via `role_required()`.

**Utility functions**:

| Function | Purpose |
|---|---|
| `is_last_active_admin(user)` | Returns `True` if `user` is the only active admin. Used to prevent deletion/deactivation of the last admin. |
| `get_staff_context()` | Returns context dict for staff pages with `users` queryset and `last_admin_ids` set. |
| `role_required(*roles)` | Decorator factory — wraps `user_passes_test` to check `user.profile.role` is in allowed roles. |

**Dashboard views**:

| View | URL | Method | Purpose |
|---|---|---|---|
| `dashboard` | `/` | GET | Renders stat cards (total, today, in production, ready) + recent 8 patients |
| `dashboard_recent` | `/dashboard/recent/` | GET | HTMX target — refreshes dashboard stats and recent patients |
| `patient_table` | `/patients/table/` | GET | Paginated, searchable, filterable patient table (8 per page) |
| `patient_list` | `/patients/list/` | GET | Full patient list page with filters |

**Patient CRUD views**:

| View | URL | Method | Purpose |
|---|---|---|---|
| `patient_form` | `/patients/form/`<br>`/patients/form/<pk>/` | GET, POST | Create (GET → empty form, POST → save) / Edit (GET → populated form, POST → update). Saves prescription snapshot if OD/OS/lens changed. |
| `patient_detail` | `/patients/<pk>/detail/` | GET | Patient details in modal + prescription history |
| `patient_update_status` | `/patients/<pk>/status/` | POST | Inline status change via dropdown |
| `patient_delete` | `/patients/<pk>/delete/` | POST (via HTMX) | Deletes patient, returns refreshed table |

**Staff management views** (all require `admin` role):

| View | URL | Method | Purpose |
|---|---|---|---|
| `staff_list` | `/staff/` | GET | Staff management page |
| `staff_create` | `/staff/create/` | POST | Creates new user with profile |
| `staff_edit` | `/staff/<pk>/edit/` | GET, POST | Edit user details, change role, reset password |
| `staff_toggle_active` | `/staff/<pk>/toggle/` | POST | Activate/deactivate user |
| `staff_delete` | `/staff/<pk>/delete/` | POST | Delete user |
| `staff_reset_password` | `/staff/<pk>/reset-password/` | POST | Reset user password |

Protections:
- Cannot delete/deactivate the last active admin.
- Cannot change the last active admin's role.
- Cannot delete yourself.

**Lens type views** (require `admin` or `optometrist`):

| View | URL | Method | Purpose |
|---|---|---|---|
| `lens_type_list` | `/settings/lens-types/` | GET | Lens type management page |
| `lens_type_create` | `/settings/lens-types/create/` | POST | Add new lens type |
| `lens_type_edit` | `/settings/lens-types/<pk>/edit/` | GET, POST | Edit lens type name |
| `lens_type_toggle` | `/settings/lens-types/<pk>/toggle/` | POST | Activate/deactivate lens type |

**Backup views** (require `admin`):

| View | URL | Method | Purpose |
|---|---|---|---|
| `backup_index` | `/settings/backup/` | GET | Shows database stats (size, counts) |
| `backup_download` | `/settings/backup/download/` | GET | Downloads `db.sqlite3` as file |
| `backup_restore` | `/settings/backup/restore/` | POST | Validates and restores uploaded backup |

**Placeholder views**:

| View | URL | Purpose |
|---|---|---|
| `appointments` | `/appointments/` | "Coming Soon" |
| `inventory` | `/inventory/` | "Coming Soon" |
| `billing` | `/billing/` | "Coming Soon" |

**HTMX pattern in views**:
Every view checks `request.headers.get('HX-Request')` to determine if it should return a partial or a full page. Partial responses use Django template partial syntax: `render(request, 'template.html#partial_name', context)`. Success/error messages are sent via `HX-Trigger` header with JSON for the toast system.

### 4.4 URL Routing

**Root** (`conf/urls.py`):
```python
urlpatterns = [
    path('admin/', admin.site.urls),       # Django admin
    path('', include('core.urls')),        # All core app routes
]
```

**Core** (`core/urls.py`):

| URL Pattern | View | Name | Auth |
|---|---|---|---|
| `/` | `dashboard` | `dashboard` | Login required |
| `/accounts/` | `django.contrib.auth.urls` | — | — |
| `/patients/table/` | `patient_table` | `patient-table` | Login required |
| `/patients/form/` | `patient_form` | `patient-create` | Login required |
| `/patients/form/<pk>/` | `patient_form` | `patient-edit` | Login required |
| `/patients/<pk>/detail/` | `patient_detail` | `patient-detail` | Login required |
| `/patients/<pk>/delete/` | `patient_delete` | `patient-delete` | Login required |
| `/patients/<pk>/status/` | `patient_update_status` | `patient-status` | Login required |
| `/dashboard/recent/` | `dashboard_recent` | `dashboard-recent` | Login required |
| `/patients/list/` | `patient_list` | `patient-list` | Login required |
| `/staff/` | `staff_list` | `staff-list` | Admin |
| `/staff/create/` | `staff_create` | `staff-create` | Admin |
| `/staff/<pk>/toggle/` | `staff_toggle_active` | `staff-toggle` | Admin |
| `/staff/<pk>/edit/` | `staff_edit` | `staff-edit` | Admin |
| `/staff/<pk>/delete/` | `staff_delete` | `staff-delete` | Admin |
| `/staff/<pk>/reset-password/` | `staff_reset_password` | `staff-reset-password` | Admin |
| `/settings/lens-types/` | `lens_type_list` | `lens-type-list` | Admin, Optometrist |
| `/settings/lens-types/create/` | `lens_type_create` | `lens-type-create` | Admin, Optometrist |
| `/settings/lens-types/<pk>/edit/` | `lens_type_edit` | `lens-type-edit` | Admin, Optometrist |
| `/settings/lens-types/<pk>/toggle/` | `lens_type_toggle` | `lens-type-toggle` | Admin, Optometrist |
| `/settings/backup/` | `backup_index` | `backup-index` | Admin |
| `/settings/backup/download/` | `backup_download` | `backup-download` | Admin |
| `/settings/backup/restore/` | `backup_restore` | `backup-restore` | Admin |
| `/appointments/` | `appointments` | `appointments` | Login required |
| `/inventory/` | `inventory` | `inventory` | Login required |
| `/billing/` | `billing` | `billing` | Login required |

### 4.5 Forms (`core/forms.py`)

**`PatientForm`** (ModelForm for `Patient`):
- Overrides `__init__` to filter `lens_type` queryset to active lens types only.
- All widgets use Tailwind CSS classes.
- Date fields use the `datepicker` class (Flatpickr picks these up automatically).
- Prescription fields are free-text (not validated to any format).

### 4.6 Admin (`core/admin.py`)

- **CustomUserAdmin**: Unregisters and re-registers `User` with `UserProfileInline` so roles appear in Django admin.
- **LensTypeAdmin**: List display includes `name` and `is_active`, `is_active` is editable in list view, searchable by name.
- **PatientAdmin**: Basic registration (no customization).
- **ClinicSettingAdmin**: Basic registration.

### 4.7 Middleware (`core/middleware.py`)

**`AutoMigrateMiddleware`**:
- Only activates in frozen (PyInstaller) mode.
- In `__init__`, it runs `call_command('migrate', '--noinput')` before any request is processed.
- This ensures the database schema is up-to-date when running from a compiled build.
- The `__call__` method simply passes through the request.

### 4.8 Signals (`core/signals.py`)

**`create_user_profile`**:
- Connected to `post_save` on `User`.
- When a new `User` is created, a `UserProfile` is automatically created.
- Superusers get role `admin`, regular users get role `staff`.
- Imported in `CoreConfig.ready()` (`core/apps.py`).

### 4.9 Context Processors (`core/context_processors.py`)

**`clinic_settings`**:
- Adds `CLINIC_NAME` to the template context for every request.
- Value comes from `ClinicSetting.load().clinic_name`.

---

## 5. Frontend — Templates

### 5.1 Base Layout (`templates/base.html`)

The root template that all pages extend.

**Head section**:
- Loads Tailwind (CDN-style via local vendor file)
- Loads HTMX, Alpine.js
- Loads Inter font, Flatpickr CSS
- Tailwind config: custom `primary` color palette (teal)
- CSRF token in `<meta>` tag
- HTMX config: injects `X-CSRFToken` header on every request
- Alpine.js re-initialization on `htmx:afterSwap`

**Body structure**:

```
├── sidebar (include "partials/sidebar.html")
├── main wrapper (lg:ml-64)
│   ├── header (sticky, with search on patient list page)
│   ├── content block
│   └── modal container (x-show="modalOpen")
└── toast notification (global Alpine component)
```

**Alpine.js data**:
- `modalOpen` (Boolean) — controls modal visibility.
- `$watch('modalOpen')` — clears modal content when closed.
- `@htmx:after-request.window` — auto-closes modal on successful table updates.

**Toast component** (lines 93–105):
- Listens for `show-message` custom event.
- Displays for 3 seconds, slides in from right.
- Two types: `success` (green) and `error` (red).

**Flatpickr initialization** (lines 108–117):
- `initDatepickers(root)` — scans for `.datepicker` class elements.
- Called on `DOMContentLoaded` and after every `htmx:afterSwap`.

### 5.2 Dashboard (`templates/dashboard.html`)

Extends `base.html`.

**Structure**:
- **Stat cards** (4 cards grid):
  - Total Patients
  - New Patients Today
  - Orders in Production (+ ready count)
- **Recent Patients table** (8 most recent):
  - Columns: Patient (with avatar, clickable for detail modal), Prescription, Contact, Lens Type, Status
  - Status is an inline dropdown (Alpine.js toggle) with HTMX POST for instant update.
- **`#patient-table-container`** (hidden by default) — populated by header search results.

**Partials defined in this template**:
- `dashboard_content` — the entire dashboard section (used by `dashboard_recent` view for HTMX refresh).
- `dashboard_recent` — just the table rows (used for inline refresh after status change).
- `patient_table` — delegates to `partials/patient_table.html` (used for search/filter results).
- `patient_form` — modal form for add/edit patient.

**Patient form modal** (lines 136–216):
- Displays in modal overlay.
- Shows full form for new patients; shows prescription/lens/status fields only when editing.
- Submits via HTMX to `/patients/form/` or `/patients/form/<pk>/`.
- On success, refreshes the patient table and shows a toast.
- On validation error, re-renders the form within the modal with error messages.

### 5.3 Patient List (`templates/patient_list.html`)

Extends `base.html`.

**Features**:
- **Header search** (in `base.html` actually): input fires `hx-get="/patients/table/"` with 300ms debounce.
- **Gender filter**: dropdown fires HTMX on change.
- **Status filter**: dropdown fires HTMX on change.
- **Patient table**: rendered by `partials/patient_table.html` inside `#patient-table-container`.
- **Add Patient button**: opens modal with patient form.

All filter inputs include each other via `hx-include` so search, gender, and status filter together.

### 5.4 Partials

#### `partials/patient_table.html`
The reusable patient table:
- **Columns**: ID (P-0001 format), Patient Name (with avatar, clickable for detail modal), Age, Gender, Contact, Prescription (OD/OS), Lens Type, Status (inline dropdown), Actions (view, edit).
- **Pagination**: Previous/Next buttons, "Page X of Y" indicator. Each button sends HTMX request with current query/filters.
- **Empty state**: "No patients found" with colspan.

#### `partials/patient_detail.html`
Modal content for patient details:
- **Header**: Large avatar, name, ID, status badge.
- **Info grid**: DOB, Age, Gender, Lens Type, Contact, Prescription (OD/OS boxes), Address, Last Visit, Patient Since, Last Updated By, Notes.
- **Prescription History** (if any): Scrollable list of previous prescriptions with date, staff name, OD, OS, lens type, notes.
- **Actions**: Close, Edit (opens edit form in modal).

#### `partials/status_badge.html`
Color-coded status display:

| Status | Color |
|---|---|
| Consultation | Blue |
| Fitting | Amber |
| In Production | Violet |
| Ready | Emerald |
| Completed | Slate |

#### `partials/sidebar.html`
Navigation sidebar (fixed left, 64-width):
- **Header**: Clinic name with eye icon.
- **Navigation links**:
  - Dashboard (always visible)
  - Patients (always visible)
  - Appointments, Inventory, Billing (all `x-show="false"` — hidden placeholders)
  - Lens Types (visible if role != staff)
  - Backup & Restore (visible if role == admin)
  - Django Admin (visible if user is superuser)
  - Staff (visible if role == admin)
- **User section** (bottom): Avatar initials, full name/username, role label, logout button.

**Role-based visibility** uses both Django template `{% if %}` and Alpine.js `x-show` (for placeholders).

### 5.5 Settings Pages

#### `settings/staff_list.html`
Admin-only page.
- **Create form**: Inline grid (First Name, Last Name, Username, Password, Role, Add button). Alpine.js `@clear-staff-form.window` resets on success.
- **Staff table**: Name, Username, Role (color-coded pill), Status (Active/Inactive with dot), Actions (Edit, Toggle Active, Delete).
- **Delete confirmation modal**: Alpine.js-driven confirmation dialog.
- **Protections**: Delete/toggle buttons hidden for last active admin and for current user.

#### `settings/lens_type_list.html`
Admin and optometrist access.
- **Create form**: Single input + button, resets on success.
- **Lens type table**: Name, Status (Active/Inactive), Actions (Edit, Toggle).

#### `settings/backup.html`
Admin-only.
- **Database Info**: Size, Last Modified, Patients count, Lens Types count, Staff count.
- **Download Backup**: Simple download link.
- **Restore from Backup**: File upload form with confirmation dialog. Shows "Restoring…" loading state via Alpine.js.

### 5.6 Login (`templates/registration/login.html`)

- **Full-screen centered** layout with gradient background.
- **Header**: Eye icon, clinic name.
- **Form**: Username, Password, Sign In button.
- **Error handling**: Django form errors shown as red alert box with "Invalid username or password" message.
- **Version**: Footer shows "v1.0.0".
- **Custom blocks**: Overrides `sidebar`, `header`, `modal_container` to be empty.
- **body_class**: Overrides to remove default sidebar layout.

---

## 6. Desktop Shell — Electron (`main.js`)

**`killBackend()`**: Terminates the Django child process. On Windows uses `taskkill /F /T` to kill the whole process tree.

**`cleanupOrphans()`**: On startup, kills any leftover `clinic-backend.exe` processes.

**`getFreePort()`**: Creates a temporary server on port 0 (OS assigns free port), gets the port number, closes the server.

**`waitForServer(port, retries=30)`**: Polls `http://127.0.0.1:<port>/` every 500ms, up to 30 retries (15 seconds total).

**`loadingPageHTML()`**: Returns an HTML page with:
- Clinic Manager logo
- Spinning loader animation
- "Loading application…" text
- Error display div (hidden by default)

**Startup flow** (`app.whenReady()`):
1. Remove application menu.
2. Create `BrowserWindow` (1280×800, menu bar hidden, `nodeIntegration: false`, `contextIsolation: true`).
3. Load loading screen (as data URL).
4. Clean up orphan processes.
5. Find a free port.
6. Determine backend path:
   - Dev with compiled exe: `dist/clinic-backend.exe`
   - Dev without exe: `python manage.py runserver`
   - Production: `process.resourcesPath/backend/clinic-backend.exe`
7. Spawn backend process, pipe stdout/stderr to console.
8. Wait for backend to respond.
9. Load the app URL in the window.
10. On failure: show error on loading screen.

**Cleanup on exit**: `before-quit`, `will-quit`, and `process.on('exit')` all call `killBackend()`.

---

## 7. HTMX Architecture

### How HTMX is used

HTMX drives all dynamic interactions without writing JavaScript:

| Interaction | Trigger | Target | Swap |
|---|---|---|---|
| Patient search | `input changed delay:300ms` | `#patient-table-container` | `innerHTML` |
| Gender/status filter | `change` | `#patient-table-container` | `innerHTML` |
| Pagination | `click` | `#patient-table-container` | `innerHTML` |
| Open add patient form | `click` on button | `#modal-container` | `innerHTML` |
| Open edit patient form | `click` on edit button | `#modal-container` | `innerHTML` |
| Save patient form | `submit` | `#patient-table-container` | `innerHTML` |
| View patient details | `click` on name | `#modal-container` | `innerHTML` |
| Update status | `click` on status option | `#status-badge-<id>` | `innerHTML` |
| Refresh dashboard | `refreshDashboardRecent` event | `#dashboard-content` | `outerHTML` |
| Delete patient | `click` on delete | `#patient-table-container` | `innerHTML` |
| Staff CRUD | various | `#staff-table-container` or modal | `innerHTML` / `outerHTML` |
| Lens type CRUD | various | `#lens-type-table-container` | `outerHTML` |

### CSRF handling
```javascript
document.addEventListener('htmx:configRequest', (e) => {
  e.detail.headers['X-CSRFToken'] = document.querySelector('meta[name="csrf-token"]')?.content;
});
```

### Partial rendering pattern
Django views use `django-template-partials` to return only a fragment:
```python
render(request, 'dashboard.html#patient_table', context)
```
The client swaps just that fragment into the target element.

### Toast notification pattern
Views return success/error messages via `HX-Trigger`:
```python
response['HX-Trigger'] = json.dumps({
    'show-message': {'text': 'Patient saved.', 'type': 'success'}
})
```
The Alpine.js toast component listens for `show-message` window events.

### Modal pattern
1. Click button → `hx-get` fetches form/detail content into `#modal-container`.
2. Alpine.js sets `modalOpen = true` → modal appears.
3. Form submit → `hx-post` sends data, target is outside the modal.
4. On success → modal auto-closes (via `htmx:after-request` event handler).
5. On validation error → `HX-Retarget: #modal-container` keeps form in modal.

---

## 8. Alpine.js Components

### Modal State (`base.html`)
```html
<div x-data="{ modalOpen: false }"
     x-init="$watch('modalOpen', val => { if (!val) document.getElementById('modal-container').innerHTML = '' })"
     @htmx:after-request.window="if($event.detail.successful && [...].includes($event.detail.target.id)) modalOpen = false">
```
- Watches `modalOpen`: clears modal content when closed.
- Auto-closes modal on successful HTMX table updates.

### Dropdown Menu (status, user actions)
```html
<div x-data="{ open: false }">
  <button @click="open = !open" @click.outside="open = false">...</button>
  <div x-show="open" @click.stop>...</div>
</div>
```
Used for status selection dropdowns in patient tables.

### Toast Notifications (`base.html`)
```html
<div x-data="{ toastMsg: '', toastType: 'success', toastShow: false }"
     @show-message.window="toastMsg = $event.detail.text; toastType = $event.detail.type; toastShow = true; setTimeout(() => toastShow = false, 3000)"
     x-show="toastShow" ...>
```
Global notification system — any component can fire a `show-message` event.

### Delete Confirmation (`settings/staff_list.html`)
```html
<section x-data="{
  deleteModalOpen: false,
  deleteUrl: '',
  deleteUsername: '',
  confirmDelete() { htmx.ajax('POST', this.deleteUrl, {target: '#staff-table-container', swap: 'outerHTML'}); }
}">
```
Uses Alpine.js for state and `htmx.ajax()` for the actual request.

### Re-initialization after HTMX swaps
```javascript
document.addEventListener('htmx:afterSwap', (e) => {
  if (typeof Alpine !== 'undefined') {
    Alpine.initTree(e.detail.elt);
  }
});
```
Ensures Alpine.js components in HTMX-loaded content work correctly.

---

## 9. Role-Based Access Control

### Decorator
```python
def role_required(*roles):
    def check(user):
        return hasattr(user, 'profile') and user.profile.role in roles
    return user_passes_test(check)
```
Applied in `urls.py`:
```python
path('staff/', views.role_required('admin')(views.staff_list), name='staff-list')
```

### Sidebar visibility

| Role | Dashboard | Patients | Lens Types | Backup & Restore | Staff | Django Admin |
|---|---|---|---|---|---|---|
| Admin | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (if superuser) |
| Optometrist | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| Staff | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |

### Last active admin protection
`is_last_active_admin(user)` checks if the user is the last active admin. Used in:
- `staff_edit` — prevents role change away from admin.
- `staff_toggle_active` — prevents deactivation.
- `staff_delete` — prevents deletion.
- In templates — hides toggle/delete buttons for the last admin.

---

## 10. Prescription History

### How it works
In `patient_form` view (lines 343–355), after saving a patient:

```python
last_rx = p.prescription_history.first()
if (not last_rx
    or last_rx.prescription_od != p.prescription_od
    or last_rx.prescription_os != p.prescription_os
    or last_rx.lens_type_id != p.lens_type_id):
    PrescriptionRecord.objects.create(
        patient=p,
        prescription_od=p.prescription_od,
        prescription_os=p.prescription_os,
        lens_type=p.lens_type,
        notes=p.notes,
        updated_by=request.user,
    )
```

A new `PrescriptionRecord` is created only when at least one of OD, OS, or lens type has changed. This avoids creating redundant history entries on every patient edit.

### Display
In `patient_detail` view (and template), the 20 most recent records are shown in reverse chronological order, displaying:
- Date of change
- Who made the change
- OD and OS values
- Lens type
- Notes

---

## 11. Backup & Restore

### Backup Download (`backup_download`)
Simply streams the SQLite file as a download named `opticare-backup-YYYY-MM-DD.sqlite3`.

### Backup Restore (`backup_restore`)
Validation pipeline:
1. **File exists** check.
2. **Size limit** — max 100 MB.
3. **SQLite header check** — reads first 16 bytes, must match `SQLite format 3\0`.
4. **Table check** — opens the uploaded file, queries `sqlite_master` for `core_patient` table.
5. **Auto-backup** — copies current database to `db.sqlite3.auto-{timestamp}`.
6. **Restore** — uses Python's `sqlite3.backup()` API to overwrite the live database atomically.
7. **Cleanup** — removes the temp file.

On any validation failure, an error toast is shown and the database is untouched.

---

## 12. Build & Distribution

### PyInstaller (`pyinstaller.spec`)

Bundles the entire Django app into a single executable:
- Runs `collectstatic` and `migrate` before building.
- Includes: `manage.py`, `conf/`, `core/`, `templates/`, `db.sqlite3`, `staticfiles/`.
- Sets `DATA_DIR` to `~/.clinic-manager` for writable files.
- Excludes heavy libraries (matplotlib, PIL, pandas, numpy, scipy, IPython, etc.) to keep bundle small.

### Electron Builder (`package.json`)

- **appId**: `com.clinic-manager.app`
- **productName**: `Clinic Manager`
- **extraResources**: Embeds `dist/clinic-backend.exe` into `backend/clinic-backend.exe` inside the package.
- **Windows target**: NSIS installer (one-click disabled, custom install directory allowed).

### Build command sequence

```bash
# 1. Build Django backend
pyinstaller pyinstaller.spec
# → dist/clinic-backend.exe

# 2. Build Electron app
npm run build
# → release/Clinic Manager Setup.exe (Windows)
```

---

## 13. Extending the App

### Adding a new model

1. **Define** in `core/models.py`.
2. **Create migration**: `python manage.py makemigrations`.
3. **Register in admin** (`core/admin.py`) if needed.
4. **Add views** in `core/views.py`.
5. **Add URLs** in `core/urls.py`.

### Adding a new view with HTMX

1. **Create the view function** in `core/views.py`.
   ```python
   @login_required
   def my_view(request):
       if request.headers.get('HX-Request'):
           return render(request, 'page.html#partial_name', context)
       return render(request, 'page.html', context)
   ```
2. **Add URL** in `core/urls.py`.
3. **Create template** with `{% partialdef partial_name %}` for HTMX fragments.
4. **Wire up** in a template with `hx-get` / `hx-post`.

### Adding a new settings page

1. **Create template** in `templates/settings/`.
2. **Create views** in `core/views.py`.
3. **Add URLs** in `core/urls.py` with appropriate role guard.
4. **Add sidebar link** in `templates/partials/sidebar.html` with `{% if user.profile.role == 'admin' %}`.

### Adding a new sidebar section

In `templates/partials/sidebar.html`:
```html
<a href="{% url 'my-page' %}" class="flex items-center gap-3 ...">
  <svg>...</svg>
  My Page
</a>
```
Use `{% if user.profile.role == 'admin' %}` for role-based visibility.

### Adding a new role

1. Add to `ROLE_CHOICES` in `UserProfile` model.
2. Create migration.
3. Update `role_required` decorator usage for new views.
4. Update sidebar visibility logic.

### Adding new static assets

Place vendor files in `core/static/vendor/js/` or `core/static/vendor/css/` and reference them in `base.html`.

For custom static files, place in `core/static/core/` and reference with `{% static 'core/myfile.js' %}`.

### Adding new database fields to Patient

1. Add field to `Patient` model in `core/models.py`.
2. Add form field in `core/forms.py` if it should be editable.
3. Add widget styling in the form class.
4. Add template markup in `partials/patient_detail.html` and `dashboard.html#patient_form`.
5. Create and run migration.

---

> This document is intended to be updated alongside code changes. Each section is self-contained — update only the relevant section when adding or modifying features.
