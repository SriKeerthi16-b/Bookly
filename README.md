# Bookly - Modern Campus Digital Library Management System

A full-featured, multi-role Django web application for college libraries.


---

## 🌟 Key Features

### 1. Dedicated Role Portals & Authentication
- 👨‍🎓 **Student Portal** (`/auth/student/login/` & `/auth/student/register/`):
  - Borrow up to 3 books for 14 days.
  - Join waitlist queues for books currently on loan with live `# in queue` ranking.
  - Interactive Daily Library Gate Pass (1-click Check In / Check Out).
  - Search catalog, filter by category/subject, and track live digital computer lab vacancy.
- 👩‍🏫 **Faculty & Research Portal** (`/auth/faculty/login/` & `/auth/faculty/register/`):
  - Extended 30-day loan duration and 6 simultaneous book quota.
  - Access peer-reviewed academic journals, research periodicals, and daily newspapers.
  - Waitlist reservation queue and gate attendance logging.
- 👩‍💼 **Librarian Control Center** (`/auth/librarian/login/` & `/auth/librarian/register/`):
  - Protected with staff security passcode (`BOOKLY-ADMIN-2026`).
  - **Full Resource Management (CRUD)**: Add, edit/update, and delete Books, Journals, Newspapers, and Computer Workstations via live modal editors.
  - **1-Click Digital Lab Workstation Switcher**: Cycle status between 🟢 Working/Vacant → 🔵 In Use → 🟠 Maintenance.
  - **Circulation Desk**: Track active loans, calculate overdue fines (₹5/day), and process 1-click book returns with automated waitlist queue notifications.
  - **Announcements Studio**: Publish campus library bulletins with category tags (Exam, New Arrivals, Maintenance, Event).
  - **Gate Attendance Logs**: Real-time record of campus library visitors and live headcount.

### 2. Comprehensive Public Catalog
- Open catalog home (`/`) with instant search, category pills, journal archives, daily newspaper counts, and computer lab vacancy summary.

---

## 🚀 Setup & Running Locally

1. Open PowerShell in this project directory:
```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py runserver
```

2. Open your browser and visit: **`http://127.0.0.1:8000/`**

---

## 🔑 Demo Accounts

| Role | Username | Password | Dedicated Login URL |
| :--- | :--- | :--- | :--- |
| **Student** | `student_keerthi` | `student@123` | `http://127.0.0.1:8000/auth/student/login/` |
| **Faculty** | `prof_sharma` | `faculty@123` | `http://127.0.0.1:8000/auth/faculty/login/` |
| **Librarian** | `librarian_admin` | `admin@123` | `http://127.0.0.1:8000/auth/librarian/login/` |

> **Librarian Passcode for New Staff Registration**: `BOOKLY-ADMIN-2026`

---

## 🛠️ Tech Stack
- **Backend**: Python 3, Django 5.x, SQLite
- **Frontend**: Django Templates, Warm Academic CSS, Plus Jakarta Sans, Lora & Cinzel typography
- **Admin**: Django Administration (`/admin/`)
- **Production Server**: Gunicorn & WhiteNoise

