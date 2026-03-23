# HR ERP Flask

Flask-based HR and employee management system with role-based access, attendance tracking, salary management, and Render-ready deployment support.

![Flask](https://img.shields.io/badge/Backend-Flask-blue)
![Database](https://img.shields.io/badge/Database-MySQL%20%2F%20PostgreSQL-lightgrey)
![Security](https://img.shields.io/badge/Security-CSRF%20%2B%20Rate%20Limiting-green)
![Deploy](https://img.shields.io/badge/Deploy-Render-46E3B7)
![License](https://img.shields.io/badge/License-MIT-brightgreen)

## Table of Contents

- [Portfolio Summary](#portfolio-summary)
- [Live Demo](#live-demo)
- [Features](#features)
- [Role Access](#role-access)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Render Deployment](#render-deployment)
- [Usage](#usage)
- [Tests](#tests)
- [Screenshots](#screenshots)
- [Recent Improvements](#recent-improvements)
- [Future Improvements](#future-improvements)
- [Contact](#contact)
- [License](#license)

## Portfolio Summary

HR ERP Flask is a lightweight but practical HR and operations management system built for small teams and internal business workflows. It focuses on employee records, attendance, salary tracking, role-based access, and production-ready deployment support through environment-based configuration.

## Live Demo

### Open Live App

```text
https://hr-erp-flask.onrender.com/login
```

- Best way to open it: copy the URL and open it in a new tab manually
- Free Render note: after opening the link, wait around `20 to 40 seconds` if the service is waking up from inactivity
- Demo note: the live app uses its own hosted database, so local database changes do not automatically appear there

### Demo Credentials

- Admin
  - Username: `admin`
  - Password: `admin123`
- Staff
  - Username: `employee`
  - Password: `employee123`

## Features

- Login, logout, and protected role-based access
- Admin and staff dashboards
- Employee management with CRUD operations
- Attendance check-in, check-out, and absent tracking
- Daily attendance overview for admin users
- Monthly attendance summary for staff users
- Salary tracking with paid and unpaid status
- Search, filtering, and pagination
- CSRF protection with Flask-WTF
- Login rate limiting with Flask-Limiter
- MySQL support for local development
- PostgreSQL support for production deployment

## Role Access

- `Admin` can manage employees, attendance records, salaries, and staff registration.
- `Staff` can access their own dashboard, attendance features, and assigned workflow views.

## Tech Stack

- Flask
- Jinja2 templates
- MySQL via `PyMySQL`
- PostgreSQL via `psycopg2-binary`
- Flask-WTF
- Flask-Limiter
- Gunicorn
- HTML, CSS, JavaScript

## Project Structure

```text
HR-ERP-Flask/
|-- app.py
|-- db.py
|-- config.py
|-- config.example.py
|-- bootstrap_db.py
|-- import_render_data.py
|-- update_login_credentials.py
|-- mineerp.sql
|-- requirements.txt
|-- Procfile
|-- static/
|   |-- css/
|   |-- js/
|   |-- images/
|   |-- erp-logo/
|-- templates/
|   |-- admin/
|   |-- attendance/
|   |-- auth/
|   |-- staff/
|   |-- base.html
|-- tests/
|-- data/
|-- README.md
```

## Installation

### 1. Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root or configure the same values in your deployment environment.

### Local MySQL example

```env
SECRET_KEY=replace-with-a-strong-secret
DB_ENGINE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_NAME=mini_erp
DB_USER=root
DB_PASSWORD=your_password_here
```

### Production PostgreSQL example

```env
SECRET_KEY=replace-with-a-strong-secret
DB_ENGINE=postgres
DATABASE_URL=postgresql://username:password@host:5432/database_name
DB_SSLMODE=require
```

### Important notes

- `SECRET_KEY` should always be set in production
- keep `DB_ENGINE=mysql` for local MySQL development
- use `DATABASE_URL` for hosted PostgreSQL environments such as Render
- registration should remain restricted to approved or active staff users

## Database Setup

The file `mineerp.sql` contains the schema and initial seed data.

### MySQL local setup

1. Create a MySQL database such as `mini_erp`
2. Import the schema:

```bash
mysql -u root -p mini_erp < mineerp.sql
```

### PostgreSQL production setup

1. Create a PostgreSQL database on Render or another hosted provider
2. Set `DATABASE_URL` in the environment
3. Import or migrate equivalent schema as needed

### Bulk import helper

If your SQL data files are stored in a folder such as `%USERPROFILE%\Desktop\data`, you can import them with:

```powershell
python import_render_data.py --db-url "<RENDER_EXTERNAL_DATABASE_URL>"
```

If the folder is different:

```powershell
python import_render_data.py --db-url "<RENDER_EXTERNAL_DATABASE_URL>" --data-dir "D:\my-data-folder"
```

This importer also creates:

- `admin` / `admin123`
- `employee` / `employee123`

### Included datasets

The repository already includes:

- `data/employees.sql`
- `data/attendance.sql`
- `data/salaries.sql`

### Update login credentials quickly

```powershell
python update_login_credentials.py --db-url "<RENDER_EXTERNAL_DATABASE_URL>" --admin-pass "<NEW_ADMIN_PASSWORD>" --staff-pass "<NEW_EMPLOYEE_PASSWORD>"
```

## Render Deployment

Recommended Render setup:

- Build command:

```text
pip install -r requirements.txt
```

- Start command:

```text
gunicorn app:app
```

- Required environment variables:
  - `SECRET_KEY`
  - `DB_ENGINE=postgres`
  - `DATABASE_URL`
  - `DB_SSLMODE=require`

Free Render note:

- the service can sleep when idle
- the first request may take `20 to 40 seconds`
- use hosted PostgreSQL for production-style persistence

## Usage

### Run locally

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

### Optional Flask CLI run

```powershell
$env:FLASK_APP="app.py"
$env:FLASK_ENV="development"
flask run
```

## Tests

```powershell
pytest -q
```

## Screenshots

### Admin Dashboard

![Admin Dashboard](static/images/AdminDashboard.PNG)

### Staff Dashboard

![Staff Dashboard](static/images/StaffDashboard.PNG)

### Employees

![Employees](static/images/Employees.PNG)

### Attendance List

![Attendance List](static/images/AttendanceList.PNG)

### Mark Attendance

![Mark Attendance](static/images/MarkAttendance.PNG)

### Salary

![Salary](static/images/Salary.PNG)

## Recent Improvements

- Added active navbar highlighting for clearer navigation
- Improved profile and dashboard presentation
- Added logo and favicon support from `static/`
- Added environment-based configuration loading
- Improved responsive layout behavior
- Added CSRF protection and login rate limiting
- Added pagination, filtering, and cleaner admin tables

## Future Improvements

- CSV export for attendance and salary
- Password reset flow
- Email notifications
- Audit log for admin activity
- More analytics and reporting widgets

## Contact

For support, collaboration, or any project-related help:

- Email: `sheikhghazi09@gmail.com`
- WhatsApp: `+923212454880`

## License

MIT
