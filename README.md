# Mini ERP (Flask)

A lightweight HR/ERP web application built with Flask.  
It provides role-based access for Admin and Staff to manage employees, attendance, and salaries.  
The project supports MySQL for local development and PostgreSQL for production deployments (e.g., Render).

## Description
Mini ERP is a simple HR management system with authentication, employee records, attendance tracking, and salary management.  
It is designed to be easy to run locally while remaining production-ready with environment-based configuration.

## Live Demo (No Installation)
Open directly in browser:
- **[https://hr-erp-flask.onrender.com/login](https://hr-erp-flask.onrender.com/login)**
After opening the link, please wait 20-40 seconds for the app to load.

## Test Credentials
**Admin Login**
- username: admin
- password: admin123

**Staff Login**
- username: employee
- password: employee123

## Features
- User authentication (login, register, logout)
- Role-based access control (Admin, Staff)
- Employee management (CRUD, search, filters, pagination)
- Attendance system (check-in, check-out, absent)
- Daily attendance overview (admin)
- Monthly attendance summary (employee)
- Salary management (monthly view, net calculation, paid/unpaid tracking)
- Admin and Staff dashboards
- Fully responsive UI (mobile, tablet, desktop)
- Server-side pagination, filtering, and sorting for attendance and salary
- CSRF protection and login rate limiting

## Tech Stack
- Python (Flask)
- MySQL (PyMySQL) / PostgreSQL (psycopg2)
- Werkzeug (password hashing)
- Flask-WTF (CSRF protection)
- Flask-Limiter (rate limiting)
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

### Included Datasets (In Repo)
These SQL datasets are also included in this repository under:
- `data/employees.sql`
- `data/attendance.sql`
- `data/salaries.sql`

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

### Run with Flask CLI (optional)
```powershell
$env:FLASK_APP="app.py"
$env:FLASK_ENV="development"
flask run
```

## Tests
```powershell
pip install -r requirements.txt
pytest -q
```

## Screenshots
- Admin Dashboard  
  ![Admin Dashboard](static/images/AdminDashboard.PNG)
- Staff Dashboard  
  ![Staff Dashboard](static/images/StaffDashboard.PNG)
- Employees  
  ![Employees](static/images/Employees.PNG)
- Attendance List  
  ![Attendance List](static/images/AttendanceList.PNG)
- Mark Attendance  
  ![Mark Attendance](static/images/MarkAttendance.PNG)
- Salary  
  ![Salary](static/images/Salary.PNG)

## Recent Updates
- Added active tab highlighting in the navbar for both admin and staff views.
- Updated staff profile card and username styling for a more professional UI.
- Logo is now loaded from `static/` and favicon set is configured in the base template.
- `.env` loader added in `config.py` to support local environment variables.
- Navbar behavior adjusted to scroll naturally with the page (no sticky/fixed lock).
- UI now uses a responsive layout system and reusable components for consistent styling.
- Added CSRF protection, login rate limiting, and server-side pagination for admin tables.

## Future Improvements
- Add CSV export for salary and attendance
- Add password reset
- Add email notifications
- Add audit log for admin actions

## Contact
For support, collaboration, or any project-related help:
- Email: `sheikhghazi09@gmail.com`
- WhatsApp: `+923212454880`

## License
MIT
