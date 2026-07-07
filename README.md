# FULafia Digital Queue Management System (DQMS)

A web-based **Digital Queue Management System** designed for **Federal University of Lafia (FULafia)**, enabling multiple university offices to independently manage student walk-in queues through a single, shared platform.

> **Final-Year Project** by **Ajunwa, Stephen Oche** (2021/CP/CSC/0295)  
> Department of Computer Science, Federal University of Lafia

---

## Features

- **Multi-Office Support** — M.I.S/ICT, Registry, Bursary, Student Affairs (and extensible to any new office with zero code changes)
- **Virtual Queue Tokens** — Students join from their phones; no physical waiting lines
- **Per-Office QR Codes** — Each office gets a unique QR code linking directly to its queue
- **FCFS (First-Come-First-Served)** — Strict ordering enforced independently within each office
- **Live Status Tracking** — Real-time position and estimated wait time via auto-polling
- **Complaint Integration** — Staff see *what* the student needs before calling them
- **Balking & Reneging** — Queue-full rejection and voluntary cancellation handled gracefully
- **Role-Based Access** — Three tiers: `staff`, `office_admin`, `super_admin`
- **Strict Office Isolation** — Staff can only see/manage their own office's queue, guaranteed at the service layer
- **Per-Office Analytics** — Average wait/service times, category breakdowns, staff leaderboards, hourly arrivals
- **University-Wide Dashboard** — Super Admin sees cross-office comparisons and totals
- **Daily Token Reset** — Token numbers restart at `#001` each day, per office
- **CSV Export** — Office admins can export queue logs by date range
- **Mobile-First** — All student-facing pages are responsive

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Web Framework | Flask 3.x |
| ORM | Flask-SQLAlchemy |
| Database | SQLite (via SQLAlchemy) |
| Migrations | Flask-Migrate (Alembic) |
| Authentication | Flask-Login + Werkzeug password hashing |
| Forms & CSRF | Flask-WTF |
| Frontend | Jinja2 + HTML5/CSS3 + Vanilla JavaScript |
| Real-time Updates | Short-interval polling (fetch every 4–5s) |
| Charts | Chart.js (CDN) |
| QR Codes | `qrcode` + `Pillow` |
| Testing | Pytest |

---

## Prerequisites

- **Python 3.11+** (or 3.10 minimum)
- **pip** (Python package manager)
- **Git** (optional, for cloning)

---

## Installation and Setup

You can set up and run the system either automatically (using the provided `.bat` scripts on Windows) or manually via standard terminal commands.

---

### Method A: Automatic Setup (Windows)

This is the easiest and fastest way to get the system running.

1. **Clone the Repository:**
   ```bash
   git clone <repository-url>
   cd Queue_Mgt
   ```
2. **Run the Setup Script:**
   Double-click `setup.bat` (or run it from a terminal: `setup.bat`). This script will automatically:
   * Create a Python virtual environment (`venv`).
   * Install all required dependencies from `requirements.txt`.
   * Create your local `.env` configuration file.
   * Initialize the SQLite database and create all required tables.
   * Seed the database with campus offices, complaint categories, staff accounts, and historical queue tokens.
3. **Start the System:**
   Double-click `start.bat` (or run it from a terminal: `start.bat`). This will launch the web application.
4. **Access the System:**
   Open your browser and navigate to **http://127.0.0.1:5000**.

---

### Method B: Manual Setup (Cross-Platform)

Follow these steps if you prefer to set up the environment manually or if you are running on macOS/Linux.

1. **Clone the Repository:**
   ```bash
   git clone <repository-url>
   cd Queue_Mgt
   ```
2. **Create a Virtual Environment:**
   ```bash
   python -m venv venv
   
   # Activate:
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```
3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure Environment:**
   Copy the example configuration file:
   ```bash
   copy .env.example .env   # Windows
   cp .env.example .env     # macOS/Linux
   ```
   *Note: Edit `.env` to configure geofencing and custom settings (see details below).*
5. **Initialize Database Tables:**
   Run the following Python command to create your SQLite database tables:
   ```bash
   python -c "from app import create_app, db; app = create_app(); ctx = app.app_context(); ctx.push(); db.create_all(); print('Database tables created successfully!')"
   ```
6. **Seed Demo Data:**
   Seed the database with sample university departments, credentials, and historical logs:
   ```bash
   python scripts/seed_data.py
   ```
7. **Run the Application:**
   ```bash
   python run.py
   ```
   Open your browser and navigate to **http://127.0.0.1:5000**.

---

## Default Login Credentials

| Role | Username | Password | Office |
|---|---|---|---|
| Super Admin | `superadmin` | `admin123` | All (university-wide) |
| MIS Admin | `mis_admin` | `admin123` | M.I.S/ICT |
| MIS Staff 1 | `mis_staff1` | `staff123` | M.I.S/ICT (Counter 1) |
| MIS Staff 2 | `mis_staff2` | `staff123` | M.I.S/ICT (Counter 2) |
| Registry Admin | `reg_admin` | `admin123` | Registry |
| Registry Staff 1 | `reg_staff1` | `staff123` | Registry (Counter 1) |
| Registry Staff 2 | `reg_staff2` | `staff123` | Registry (Counter 2) |
| Bursary Admin | `bur_admin` | `admin123` | Bursary |
| Bursary Staff 1 | `bur_staff1` | `staff123` | Bursary (Counter 1) |
| Bursary Staff 2 | `bur_staff2` | `staff123` | Bursary (Counter 2) |
| Student Affairs Admin | `sa_admin` | `admin123` | Student Affairs |
| Student Affairs Staff 1 | `sa_staff1` | `staff123` | Student Affairs (Counter 1) |
| Student Affairs Staff 2 | `sa_staff2` | `staff123` | Student Affairs (Counter 2) |

### Sample Student Matric Numbers (for testing/demo)

Students join queues by verifying their Matric Number. Here are some seeded student accounts:

| Matric Number | Full Name | Department |
|---|---|---|
| `2021/CP/CSC/0295` | Ajunwa Stephen Oche | Computer Science |
| `2021/NS/CSC/0101` | Chinedu Okonkwo | Computer Science |
| `2022/CP/CSC/0202` | Abubakar Sadiq Ibrahim | Computer Science |
| `2020/AR/PHY/0055` | Ngozi Adaeze Nwosu | Physics |
| `2021/NS/PHY/0078` | Mohammed Kabir Yusuf | Physics |

---

## Project Structure

```
Queue_Mgt/
├── app/
│   ├── __init__.py                 # App factory (create_app)
│   ├── config.py                   # Config classes (Dev/Test/Prod)
│   ├── extensions.py               # db, login_manager, migrate, csrf
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── office.py               # Office model
│   │   ├── complaint_category.py   # Per-office category list
│   │   ├── student.py              # Student model (shared across offices)
│   │   ├── staff.py                # Staff model (role-based)
│   │   ├── complaint.py            # Complaint model (office-scoped)
│   │   ├── queue_token.py          # QueueToken model (per-office daily numbering)
│   │   └── system_setting.py       # Global fallback defaults
│   │
│   ├── blueprints/
│   │   ├── main/                   # Office directory landing page
│   │   ├── student/                # Student registration & status
│   │   ├── staff/                  # Staff dashboard & queue ops
│   │   ├── office_admin/           # Office-level admin dashboard
│   │   ├── super_admin/            # University-wide admin
│   │   ├── auth/                   # Login/logout
│   │   └── api/                    # JSON API endpoints
│   │
│   ├── services/
│   │   ├── queue_service.py        # Core queue logic (FCFS, balking, etc.)
│   │   ├── wait_time_service.py    # Per-office wait estimation
│   │   ├── analytics_service.py    # Per-office + cross-office analytics
│   │   └── qr_service.py          # QR code generation
│   │
│   ├── static/                     # CSS, JS, images
│   ├── templates/                  # Jinja2 templates
│   └── utils/                      # Decorators, validators
│
├── tests/
│   ├── conftest.py                 # Pytest fixtures
│   ├── test_models.py             # Model unit tests
│   ├── test_queue_service.py      # Queue service tests
│   ├── test_wait_time_service.py  # Wait time estimation tests
│   ├── test_multi_office_isolation.py  # CRITICAL office isolation tests
│   └── test_api.py               # API endpoint tests
│
├── scripts/
│   └── seed_data.py               # Database seeder
│
├── migrations/                     # Alembic migration files
├── instance/                       # SQLite database file
│
├── .env.example                    # Environment template
├── .gitignore
├── requirements.txt
├── run.py                          # Application entry point
└── README.md                       # This file
```

---

## Running Tests

Run the full test suite with:

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```

Run a specific test file:

```bash
pytest tests/test_multi_office_isolation.py -v
```

Run with coverage report:

```bash
pip install pytest-cov
pytest --cov=app --cov-report=term-missing
```

### Key Test Files

| File | Purpose |
|---|---|
| `test_models.py` | Model creation, uniqueness, password hashing |
| `test_queue_service.py` | FCFS ordering, token numbering, balking, cancel |
| `test_wait_time_service.py` | Wait estimation with/without history |
| `test_multi_office_isolation.py` | **CRITICAL** — proves offices can never see each other's data |
| `test_api.py` | API endpoint responses, auth, cross-office 403s |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/offices` | List all active offices |
| `POST` | `/api/queue/join` | Join an office's queue |
| `GET` | `/api/queue/status/<id>` | Get token status, position, and wait estimate |
| `POST` | `/api/queue/cancel/<id>` | Cancel a waiting token |
| `GET` | `/api/staff/waitlist` | Get staff's office waitlist (auth required) |
| `POST` | `/api/staff/call-next` | Call the next waiting student (auth required) |
| `POST` | `/api/staff/complete/<id>` | Mark token as completed (auth required) |
| `POST` | `/api/staff/skip/<id>` | Mark token as skipped (auth required) |
| `GET` | `/api/office-admin/analytics` | Office analytics (auth required) |
| `GET` | `/api/super-admin/analytics` | University-wide analytics (auth required) |

---

## Screenshots

> Screenshots will be added after the application is deployed.

---

## Offices Supported

| Office | Slug | Capacity | Counters | Hours |
|---|---|---|---|---|
| M.I.S/ICT | `mis` | 50 | 3 | 08:00 – 16:00 |
| Registry | `registry` | 40 | 2 | 08:00 – 16:00 |
| Bursary | `bursary` | 60 | 3 | 08:00 – 15:00 |
| Student Affairs | `student-affairs` | 30 | 2 | 09:00 – 16:00 |

> New offices can be added by the Super Admin via the admin dashboard — **no code changes required**.

---

## License

This project is licensed under the **MIT License**.

---

## Author

**Ajunwa, Stephen Oche**  
Matric No: 2021/CP/CSC/0295  
Department of Computer Science  
Federal University of Lafia, Nasarawa State, Nigeria

---

*Built as a final-year project to demonstrate a scalable, multi-office digital queue management solution for Nigerian universities.*
