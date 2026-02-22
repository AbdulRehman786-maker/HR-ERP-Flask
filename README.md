# Mini ERP (Flask)

A lightweight HR/ERP web application built with Flask.  
It provides role-based access for Admin and Staff to manage employees, attendance, and salaries.  
The project supports MySQL for local development and PostgreSQL for production deployments (e.g., Render).

## Description
Mini ERP is a simple HR management system with authentication, employee records, attendance tracking, and salary management.  
It is designed to be easy to run locally while remaining production-ready with environment-based configuration.

## Live Demo (No Installation)
Open directly in browser:
- `https://hr-erp-flask.onrender.com/login`

## Test Credentials
**Admin Login**
- username: admin
- password: set via `update_login_credentials.py`

**Staff Login**
- username: employee
- password: set via `update_login_credentials.py`

> Security Note: Never commit real passwords in README or source code.

## Features
- User authentication (login, register, logout)
- Role-based access control (Admin, Staff)
- Employee management (CRUD, search, filters, pagination)
- Attendance system (check-in, check-out, absent)
- Daily attendance overview (admin)
- Monthly attendance summary (employee)
- Salary management (monthly view, net calculation, paid/unpaid tracking)
- Admin and Staff dashboards

## Tech Stack
- Python (Flask)
- MySQL (PyMySQL) / PostgreSQL (psycopg2)
- Werkzeug (password hashing)
- HTML/CSS (Jinja templates)

## Project Structure
```
C:.
|   .env
|   .gitignore
|   app.py
|   config.example.py
|   config.py
|   db.py
|   mineerp.sql
|   requirements.txt
|   Procfile
|
|---static
|   |---css
|   |       style.css
|   |
|   |---js
|           app.js
|
|---templates
|   |   base.html
|   |
|   |---admin
|   |       attendance.html
|   |       dashboard.html
|   |       employees.html
|   |       employee_form.html
|   |       salary.html
|   |
|   |---attendance
|   |       attendance.html
|   |
|   |---auth
|   |       login.html
|   |       register.html
|   |
|   |---staff
|           dashboard.html
```

## Installation
### 1) Clone and create a virtual environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2) Install dependencies
```powershell
pip install -r requirements.txt
```

## Setup / Environment Variables
Create a `.env` file in the project root (or set variables in your shell / Render dashboard).

**Required (all environments):**
```
SECRET_KEY=replace-me
DB_ENGINE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_NAME=mini_erp
DB_USER=root
DB_PASSWORD=your_password_here
```

**Production (PostgreSQL / Render):**
```
DB_ENGINE=postgres
DATABASE_URL=postgres://user:pass@host:5432/dbname
DB_SSLMODE=require
SECRET_KEY=your-strong-secret
```

**Important Notes**
- `SECRET_KEY` must be set for production.
- For Render, use the **DATABASE_URL** provided by Render.
- Keep `DB_ENGINE=mysql` for local MySQL development.

## Database Setup
The SQL file `mineerp.sql` contains the schema and seed data.

### MySQL (Local)
1. Create a database (example: `mini_erp`)
2. Import schema:
```bash
mysql -u root -p mini_erp < mineerp.sql
```

### PostgreSQL (Production)
1. Create a PostgreSQL database on Render.
2. Use the provided `DATABASE_URL`.
3. Import schema manually if needed (convert or use equivalent SQL).

### Bulk Import from SQL Files
If you keep data files in your Desktop `data` folder (example: `%USERPROFILE%\Desktop\data`) as:
- `employees.sql`
- `attendance.sql`
- `salaries.sql`

Use this command to import all data to Render PostgreSQL and create login users:

```powershell
python import_render_data.py --db-url "<RENDER_EXTERNAL_DATABASE_URL>"
```

If your data folder is different, pass it explicitly:

```powershell
python import_render_data.py --db-url "<RENDER_EXTERNAL_DATABASE_URL>" --data-dir "D:\my-data-folder"
```

This importer also creates:
- `admin` / `admin123`
- `employee` / `employee123`

### Update Login Passwords Quickly
```powershell
python update_login_credentials.py --db-url "<RENDER_EXTERNAL_DATABASE_URL>" --admin-pass "<NEW_ADMIN_PASSWORD>" --staff-pass "<NEW_EMPLOYEE_PASSWORD>"
```

## Usage
### Run locally (development)
```powershell
python app.py
```
Then open your browser at: `http://127.0.0.1:5000`

## Screenshots
- Admin Dashboard  
  ![Admin Dashboard](static/AdminDashboard.PNG)
- Staff Dashboard  
  ![Staff Dashboard](static/StaffDashboard.PNG)
- Mark Attendance  
  ![Mark Attendance](static/MarkAttendance.PNG)
- Salary  
  ![Salary](static/Salary.PNG)

## Recent Updates
- Added active tab highlighting in the navbar for both admin and staff views.
- Updated staff profile card and username styling for a more professional UI.
- Logo is now loaded from `static/` and favicon set is configured in the base template.
- `.env` loader added in `config.py` to support local environment variables.
- Navbar behavior adjusted to scroll naturally with the page (no sticky/fixed lock).

## Future Improvements
- Add CSV export for salary and attendance
- Add password reset
- Add email notifications
- Improve UI/UX responsiveness

## License
MIT
