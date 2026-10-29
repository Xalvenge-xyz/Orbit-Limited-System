# ORBIT POS & Telemetry System

Full-stack POS and business management system with NASA mission-control UI.

## Stack
- Backend: Python / Flask (SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF)
- Database: MySQL via XAMPP (`orbit_pos`)
- Frontend: HTML/CSS/Vanilla JS + Chart.js

## Setup (Windows + XAMPP)
1. Install Python 3.11+ and XAMPP.
2. Start MySQL in XAMPP control panel.
3. Create database:
   ```sql
   CREATE DATABASE orbit_pos CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
4. Create venv and install deps:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```
5. Configure `.env` (copy `.env.example`).
6. Run migrations:
   ```powershell
   $env:FLASK_APP='app.py'
   python -m flask db upgrade
   ```
7. Create initial owner:
   ```powershell
   python seed_owner.py
   ```
   (Or use /auth/setup-owner before any users exist.)
8. Run app:
   ```powershell
   python app.py
   ```
   Open http://127.0.0.1:5000

## Tests
```powershell
python -m pytest
```

## Default owner
- Email: owner@orbit.local
- Password: password123 (change after first login)

## Backup
Use `mysqldump -u root orbit_pos > backup.sql`.
