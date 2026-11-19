# Smart Campus Facility Booking and Maintenance Platform

## Windows setup
Open PowerShell in this folder and run:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m backend.app
```
If PowerShell blocks activation, run `python -m pip install -r requirements.txt` without activating the environment. Open http://127.0.0.1:5000.

## Demo accounts
- Student: `student` / `student123`
- Faculty: `faculty` / `faculty123`
- Facility Manager: `manager` / `manager123`
- Technician: `technician` / `tech123`
- Approver: `approver` / `approve123`
- Administrator: `admin` / `admin123`

These are demonstration credentials only.

## Docker
Start Docker Desktop, then run `docker compose up --build`. Open http://127.0.0.1:5000. SQLite data persists in `database/smartcampus.db`.

## Included
Login with server-side sessions, dashboard, facility catalogue, booking requests, approval/rejection, backend overlap check at approval, maintenance tickets, keyword-based priority suggestion (not ML), technician assignment and updates, audit history.

## Academic limitation
This is a prototype with synthetic data, one Flask instance and SQLite. A genuine two-backend-instance test should use a shared PostgreSQL database; do not claim 300 concurrent users without measured load-test evidence. Change the demo secret and passwords before deployment.
