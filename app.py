from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from calendar import monthrange
from functools import wraps
from config import Config
from db import get_db_connection

app = Flask(__name__)
app.config.from_object(Config)
app.config.setdefault("WTF_CSRF_TIME_LIMIT", None)
csrf = CSRFProtect(app)
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])


def _page_range(current_page: int, total_pages: int, window: int = 2):
    start_page = max(1, current_page - window)
    end_page = min(total_pages, current_page + window)
    return range(start_page, end_page + 1)

@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static", "erp-logo"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


# ---------- Decorators for Access Control ----------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session or session.get("role") != "admin":
            flash("Access denied!", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# ---------- Authentication Routes ----------
@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
@csrf.exempt
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("All fields are required", "warning")
            return redirect(url_for("login"))

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT u.*, e.status, e.role AS emp_role
                FROM users u
                JOIN employees e ON u.emp_id = e.emp_id
                WHERE u.username = %s
            """, (username,))
            user = cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

        role = (user.get("emp_role") if user else None) or (user.get("role") if user else None)
        if user and user["status"] == "active" and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            session["role"] = role
            session["emp_id"] = user["emp_id"]

            if role == "admin":
                flash("Login successful. Welcome back!", "success")
                return redirect(url_for("admin_dashboard"))
            elif role == "staff":
                flash("Login successful. Welcome back!", "success")
                return redirect(url_for("staff_dashboard"))
            else:
                flash("Invalid role. Contact administrator.", "warning")
                return redirect(url_for("login"))

        flash("Invalid username or password.", "danger")
        return redirect(url_for("login"))

    return render_template("auth/login.html")

@app.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute")
@csrf.exempt
def register():
    if request.method == "POST":
        emp_id = request.form.get("emp_id", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not emp_id or not username or not password:
            flash("All fields are required", "warning")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check employee exists & active
        cursor.execute("SELECT role FROM employees WHERE emp_id = %s AND status = 'active'", (emp_id,))
        employee = cursor.fetchone()
        if not employee:
            flash("Invalid or inactive Employee ID", "warning")
            cursor.close()
            conn.close()
            return redirect(url_for("register"))

        # Check emp_id already has account
        cursor.execute("SELECT user_id FROM users WHERE emp_id = %s", (emp_id,))
        if cursor.fetchone():
            flash("Account already exists for this Employee ID", "info")
            cursor.close()
            conn.close()
            return redirect(url_for("login"))

        # Check username unique
        cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            flash("Username already taken", "warning")
            cursor.close()
            conn.close()
            return redirect(url_for("register"))

        # Insert user with role from employee
        cursor.execute("""
            INSERT INTO users (emp_id, username, password_hash, role)
            VALUES (%s, %s, %s, %s)
        """, (emp_id, username, password_hash, employee["role"]))

        conn.commit()
        cursor.close()
        conn.close()

        flash("Account created successfully", "success")
        return redirect(url_for("login"))

    return render_template("auth/register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully", "success")
    return redirect(url_for("login"))

# ---------- Admin Routes ----------
@app.route("/admin/dashboard")
@login_required
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(emp_id) AS total_employees FROM employees")
    total_employees = cursor.fetchone().get("total_employees", 0)

    cursor.execute("""
        SELECT COUNT(emp_id) AS present_employees
        FROM attendance
        WHERE LOWER(status) = 'present' AND attendance_date = CURRENT_DATE
    """)
    present_employees = cursor.fetchone().get("present_employees", 0)

    cursor.execute("""
        SELECT COUNT(emp_id) AS unpaid_employees
        FROM salaries
        WHERE LOWER(paid_status) = 'unpaid'
    """)
    unpaid_employees = cursor.fetchone().get("unpaid_employees", 0)

    cursor.close()
    conn.close()

    return render_template(
        "admin/dashboard.html",
        total_employees=total_employees,
        UnPaidEmplyees=unpaid_employees,
        PresentEmployees=present_employees
    )


@app.route("/admin/employees")
@login_required
@admin_required
def admin_employees():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get filter parameters
    department = request.args.get("department", "").strip()
    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "asc").lower()
    page = request.args.get("page", 1, type=int)
    if page < 1: 
        page = 1

    limit = 10
    offset = (page - 1) * limit

    # Build query conditions
    base_query = "FROM employees WHERE 1=1"
    params = []

    if q:
        if q.isdigit():
            base_query += " AND emp_id = %s"
            params.append(int(q))
        else:
            base_query += " AND CONCAT(first_name,' ',last_name) LIKE %s"
            params.append(f"%{q}%")

    if department:
        base_query += " AND LOWER(department) = LOWER(%s)"
        params.append(department)

    # Get total count
    cursor.execute(f"SELECT COUNT(*) AS total {base_query}", tuple(params))
    total_records = cursor.fetchone()["total"]
    total_pages = (total_records + limit - 1) // limit

    # Get paginated data
    order = "DESC" if sort == "descending" else "ASC"
    cursor.execute(
        f"SELECT emp_id, first_name, last_name, phone, department, role {base_query} ORDER BY emp_id {order} LIMIT %s OFFSET %s",
        tuple(params + [limit, offset])
    )
    employees = cursor.fetchall()

    cursor.execute("SELECT DISTINCT department FROM employees WHERE department IS NOT NULL ORDER BY department ASC")
    departments = [row["department"] for row in cursor.fetchall() if row.get("department")]

    cursor.close()
    conn.close()

    # Pagination range
    window = 2 
    start_page = max(1, page - window)
    end_page = min(total_pages, page + window)
    page_range = range(start_page, end_page + 1)

    return render_template(
        "admin/employees.html",
        employees=employees,
        total_records=total_records,
        total_pages=total_pages,
        current_page=page,
        page_range=page_range,
        q=q,
        department=department,
        sort=sort,
        departments=departments,
    )

@app.route("/admin/employees/new", methods=["GET", "POST"])
@login_required
@admin_required
def admin_employee_new():
    if request.method == "POST":
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO employees(first_name, last_name, email, phone, department, role)
                        VALUES (%s, %s, %s, %s, %s, %s)""",
            (request.form.get("first_name"),
             request.form.get("last_name"),
             request.form.get("email"),
             request.form.get("phone"),
             request.form.get("department"),
             request.form.get("role")))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Employee added successfully", "success")
        return redirect(url_for("admin_employees"))
    
    return render_template("admin/employee_form.html")

@app.route("/admin/employees/<int:employee_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def admin_employee_edit(employee_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == "POST":
        cursor.execute("""UPDATE employees SET first_name = %s, last_name = %s, email = %s, 
                       phone = %s, department = %s, role = %s WHERE emp_id = %s""", 
                       (request.form.get("first_name"),
                        request.form.get("last_name"),
                        request.form.get("email"),
                        request.form.get("phone"),
                        request.form.get("department"),
                        request.form.get("role"),
                        employee_id))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Employee updated successfully", "success")
        return redirect(url_for("admin_employees"))
    
    cursor.execute("SELECT * FROM employees WHERE emp_id=%s", (employee_id,))
    employee = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not employee:
        flash("Employee not found", "warning")
        return redirect(url_for("admin_employees"))
        
    return render_template("admin/employee_form.html", employee=employee)

@app.route("/admin/employees/<int:employee_id>/delete", methods=["POST"])
@login_required
@admin_required
def admin_employee_delete(employee_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees WHERE emp_id = %s", (employee_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Employee deleted successfully", "success")
    return redirect(url_for("admin_employees"))

@app.route("/admin/attendance")
@login_required
@admin_required
def admin_attendance():
    conn = get_db_connection()
    cursor = conn.cursor()
    engine = (Config.DB_ENGINE or "mysql").lower()
    time_expr = (
        "COALESCE(TO_CHAR(a.check_in, 'HH24:MI'), '--:--')"
        if engine.startswith("post")
        else "COALESCE(TIME_FORMAT(a.check_in, '%%H:%%i'), '--:--')"
    )
    time_expr_out = (
        "COALESCE(TO_CHAR(a.check_out, 'HH24:MI'), '--:--')"
        if engine.startswith("post")
        else "COALESCE(TIME_FORMAT(a.check_out, '%%H:%%i'), '--:--')"
    )

    attendance_date = request.args.get("date", "").strip()
    emp_id_raw = request.args.get("emp_id", "").strip()
    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "").strip().lower()
    order = request.args.get("order", "desc").strip().lower()
    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1
    limit = 10
    offset = (page - 1) * limit

    if not attendance_date:
        attendance_date = date.today().isoformat()

    emp_id = int(emp_id_raw) if emp_id_raw.isdigit() else None

    if emp_id:
        # Get month summary for specific employee
        try:
            sel = datetime.strptime(attendance_date, "%Y-%m-%d").date()
        except ValueError:
            sel = date.today()
        
        year, month = sel.year, sel.month
        month_start = date(year, month, 1).isoformat()
        last_day = monthrange(year, month)[1]
        month_end = date(year, month, last_day).isoformat()

        # Get attendance for the month
        order_dir = "ASC" if order == "asc" else "DESC"
        sort_map = {
            "date": "a.attendance_date",
            "status": "a.status",
            "check_in": "a.check_in",
            "check_out": "a.check_out",
        }
        sort_col = sort_map.get(sort, "a.attendance_date")

        count_query = """
            SELECT COUNT(*) AS total
            FROM attendance a
            WHERE a.emp_id = %s
              AND DATE(a.attendance_date) BETWEEN %s AND %s
        """
        cursor.execute(count_query, (emp_id, month_start, month_end))
        total_records = cursor.fetchone()["total"]
        total_pages = (total_records + limit - 1) // limit

        query = f"""
            SELECT
                a.attendance_date AS date,
                a.emp_id AS emp_id,
                CONCAT(e.first_name, ' ', e.last_name) AS full_name,
                {time_expr} AS check_in,
                {time_expr_out} AS check_out,
                UPPER(a.status) AS status
            FROM attendance a
            JOIN employees e ON a.emp_id = e.emp_id
            WHERE a.emp_id = %s
              AND DATE(a.attendance_date) BETWEEN %s AND %s
            ORDER BY {sort_col} {order_dir}
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (emp_id, month_start, month_end, limit, offset))
        attendance = cursor.fetchall()

        # Get summary counts
        cursor.execute("""
            SELECT
                SUM(CASE WHEN LOWER(status) = 'present' THEN 1 ELSE 0 END) AS present_days,
                SUM(CASE WHEN LOWER(status) IN ('leave', 'on leave', 'vacation', 'sick') THEN 1 ELSE 0 END) AS leave_days,
                SUM(CASE WHEN LOWER(status) IN ('absent', 'a', 'absent ', 'not present') THEN 1 ELSE 0 END) AS absent_days
            FROM attendance
            WHERE emp_id = %s
              AND DATE(attendance_date) BETWEEN %s AND %s
            """, (emp_id, month_start, month_end))
        summary = cursor.fetchone()

        cursor.close()
        conn.close()

        return render_template(
            "admin/attendance.html",
            attendance=attendance,
            mode="employee",
            attendance_date=attendance_date,
            emp_id=emp_id,
            q=q,
            sort=sort or "date",
            order=order,
            total_pages=total_pages,
            current_page=page,
            page_range=_page_range(page, total_pages),
            month_start=month_start,
            month_end=month_end,
            present_days=int(summary.get("present_days") or 0),
            leave_days=int(summary.get("leave_days") or 0),
            absent_days=int(summary.get("absent_days") or 0)
        )
    else:
        # Get attendance for all employees on specific date
        name_expr = (
            "LOWER(CONCAT(e.first_name, ' ', e.last_name))"
            if engine.startswith("post")
            else "LOWER(CONCAT(e.first_name,' ',e.last_name))"
        )
        emp_expr = "CAST(e.emp_id AS TEXT)" if engine.startswith("post") else "CAST(e.emp_id AS CHAR)"

        base_query = f"""
            FROM attendance a
            JOIN employees e ON a.emp_id = e.emp_id
            WHERE DATE(a.attendance_date) = %s
        """
        params = [attendance_date]
        if q:
            base_query += f" AND ({name_expr} LIKE %s OR {emp_expr} LIKE %s)"
            like_q = f"%{q.lower()}%"
            params.extend([like_q, like_q])

        order_dir = "ASC" if order == "asc" else "DESC"
        sort_map = {
            "date": "a.attendance_date",
            "emp_id": "e.emp_id",
            "name": "e.first_name",
            "check_in": "a.check_in",
            "check_out": "a.check_out",
            "status": "a.status",
        }
        sort_col = sort_map.get(sort, "")
        order_by = f" ORDER BY {sort_col} {order_dir}" if sort_col else " ORDER BY a.status ASC, a.check_in ASC"

        cursor.execute(f"SELECT COUNT(*) AS total {base_query}", tuple(params))
        total_records = cursor.fetchone()["total"]
        total_pages = (total_records + limit - 1) // limit

        query = f"""
            SELECT
                a.attendance_date AS date,
                e.emp_id AS emp_id,
                CONCAT(e.first_name, ' ', e.last_name) AS full_name,
                {time_expr} AS check_in,
                {time_expr_out} AS check_out,
                UPPER(a.status) AS status
            {base_query}
            {order_by}
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, tuple(params + [limit, offset]))
        attendance = cursor.fetchall()

        # Get totals for the date
        cursor.execute("""
            SELECT
                SUM(CASE WHEN LOWER(status) = 'present' THEN 1 ELSE 0 END) AS present_count,
                SUM(CASE WHEN LOWER(status) IN ('leave', 'on leave', 'vacation', 'sick') THEN 1 ELSE 0 END) AS leave_count,
                SUM(CASE WHEN LOWER(status) IN ('absent', 'a', 'absent ', 'not present') THEN 1 ELSE 0 END) AS absent_count
            FROM attendance
            WHERE DATE(attendance_date) = %s
            """, (attendance_date,))
        totals = cursor.fetchone()

        cursor.close()
        conn.close()

        return render_template(
            "admin/attendance.html",
            attendance=attendance,
            mode="date",
            attendance_date=attendance_date,
            q=q,
            sort=sort,
            order=order,
            total_pages=total_pages,
            current_page=page,
            page_range=_page_range(page, total_pages),
            present_count=int(totals.get("present_count") or 0),
            leave_count=int(totals.get("leave_count") or 0),
            absent_count=int(totals.get("absent_count") or 0)
        )

@app.route("/admin/salary")
@login_required
@admin_required
def admin_salary():
    conn = get_db_connection()
    cursor = conn.cursor()
    engine = (Config.DB_ENGINE or "mysql").lower()

    raw_month = request.args.get("month")
    emp_id_raw = request.args.get("emp_id", "").strip()
    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "").strip().lower()
    order = request.args.get("order", "asc").strip().lower()
    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1
    limit = 10
    offset = (page - 1) * limit

    # Parse month input
    if raw_month:
        try:
            dt = datetime.strptime(raw_month, "%Y-%m")  # expects YYYY-MM
        except ValueError:
            dt = datetime.today()
    else:
        dt = datetime.today()

    month_input = dt.strftime("%b-%Y")  # display like Feb-2026
    year_val = dt.year
    month_val = dt.month

    emp_id = int(emp_id_raw) if emp_id_raw.isdigit() else None

    # Build query (use created_at for month+year filter)
    base_query = """
        FROM employees e
        JOIN salaries s ON s.emp_id = e.emp_id
        WHERE EXTRACT(YEAR FROM s.created_at) = %s
          AND EXTRACT(MONTH FROM s.created_at) = %s
    """
    params = [year_val, month_val]

    if emp_id:
        base_query += " AND e.emp_id = %s"
        params.append(emp_id)

    if q:
        name_expr = (
            "LOWER(CONCAT(e.first_name, ' ', e.last_name))"
            if engine.startswith("post")
            else "LOWER(CONCAT(e.first_name,' ',e.last_name))"
        )
        emp_expr = "CAST(e.emp_id AS TEXT)" if engine.startswith("post") else "CAST(e.emp_id AS CHAR)"
        base_query += f" AND ({name_expr} LIKE %s OR {emp_expr} LIKE %s)"
        like_q = f"%{q.lower()}%"
        params.extend([like_q, like_q])

    sort_map = {
        "emp_id": "e.emp_id",
        "employee": "e.first_name",
        "base": "s.base_salary",
        "bonus": "s.bonus",
        "deductions": "s.deductions",
        "net": "(s.base_salary + s.bonus - s.deductions)",
        "status": "s.paid_status",
    }
    order_dir = "DESC" if order == "desc" else "ASC"
    sort_col = sort_map.get(sort, "e.emp_id")

    # Total counts + aggregates
    cursor.execute(
        f"""
        SELECT
            COUNT(*) AS rows,
            SUM(CASE WHEN s.paid_status = 'paid' THEN 1 ELSE 0 END) AS paid,
            SUM(CASE WHEN s.paid_status != 'paid' THEN 1 ELSE 0 END) AS unpaid,
            COALESCE(SUM(s.base_salary), 0) AS base,
            COALESCE(SUM(s.bonus), 0) AS bonus,
            COALESCE(SUM(s.deductions), 0) AS deductions
        {base_query}
        """,
        tuple(params),
    )
    agg = cursor.fetchone()
    total_records = int(agg.get("rows") or 0)
    total_pages = (total_records + limit - 1) // limit

    salary_query = f"""
        SELECT
            e.emp_id,
            COALESCE(e.first_name, '') AS first_name,
            COALESCE(e.last_name, '') AS last_name,
            COALESCE(s.base_salary, 0) AS base_salary,
            COALESCE(s.bonus, 0) AS bonus,
            COALESCE(s.deductions, 0) AS deductions,
            COALESCE(s.paid_status, 'unpaid') AS paid_status,
            s.created_at
        {base_query}
        ORDER BY {sort_col} {order_dir}
        LIMIT %s OFFSET %s
    """

    cursor.execute(salary_query, tuple(params + [limit, offset]))
    rows = cursor.fetchall()

    # Process salary data
    salaries = []
    totals = {
        "base": float(agg.get("base") or 0),
        "bonus": float(agg.get("bonus") or 0),
        "deductions": float(agg.get("deductions") or 0),
        "net": 0,
    }
    totals["net"] = totals["base"] + totals["bonus"] - totals["deductions"]
    counts = {
        "paid": int(agg.get("paid") or 0),
        "unpaid": int(agg.get("unpaid") or 0),
        "rows": total_records,
    }

    for r in rows:
        base_salary = float(r["base_salary"])
        bonus = float(r["bonus"])
        deductions = float(r["deductions"])
        net = base_salary + bonus - deductions
        status = r["paid_status"]

        salaries.append({
            "emp_id": r["emp_id"],
            "full_name": f"{r['first_name']} {r['last_name']}".strip(),
            "base_salary": base_salary,
            "bonus": bonus,
            "deductions": deductions,
            "net": net,
            "paid_status": status,
        })

    cursor.close()
    conn.close()

    return render_template(
        "admin/salary.html",
        salaries=salaries,
        totals=totals,
        counts=counts,
        month_display=month_input,
        emp_id=emp_id,
        q=q,
        sort=sort,
        order=order,
        total_pages=total_pages,
        current_page=page,
        page_range=_page_range(page, total_pages)
    )


# ---------- General Attendance Route ----------
@app.route("/attendance", methods=["GET", "POST"])
@login_required
def attendance():
    if request.method == "POST":
        emp_id = request.form.get("emp_id")
        action = request.form.get("action")  # checkin / checkout / absent

        if not emp_id:
            flash("Employee ID is required", "warning")
            return redirect(url_for("attendance"))

        today = date.today()
        now_time = datetime.now().time()
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check today's record
        cursor.execute("SELECT * FROM attendance WHERE emp_id = %s AND attendance_date = %s", (emp_id, today))
        record = cursor.fetchone()

        if action == "checkin":
            if record:
                flash("Attendance already marked today", "info")
            else:
                cursor.execute("""
                    INSERT INTO attendance (emp_id, attendance_date, check_in, status)
                    VALUES (%s, %s, %s, 'present')
                """, (emp_id, today, now_time))
                conn.commit()
                flash("Check-in successful", "success")

        elif action == "checkout":
            if not record or not record["check_in"]:
                flash("Please check-in first", "warning")
            elif record["check_out"]:
                flash("Already checked out", "info")
            else:
                cursor.execute("""
                    UPDATE attendance SET check_out = %s
                    WHERE attendance_id = %s
                """, (now_time, record["attendance_id"]))
                conn.commit()
                flash("Check-out successful", "success")

        elif action == "absent":
            if record:
                flash("Attendance already exists today", "info")
            else:
                cursor.execute("""
                    INSERT INTO attendance (emp_id, attendance_date, status)
                    VALUES (%s, %s, 'absent')
                """, (emp_id, today))
                conn.commit()
                flash("Marked absent", "success")

        cursor.close()
        conn.close()
        return redirect(url_for("attendance"))

    return render_template("attendance/attendance.html")

# ---------- Staff Routes ----------
@app.route("/staff_dashboard")
@login_required
def staff_dashboard():
    if session.get("role") != "staff":
        flash("Access denied!", "warning")
        return redirect(url_for("login"))

    emp_id = session.get("emp_id")
    if not emp_id:
        flash("Session expired. Please login again.", "warning")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.username, u.role AS user_role,
               e.emp_id, e.first_name, e.last_name, e.department, e.email
        FROM users u
        JOIN employees e ON u.emp_id = e.emp_id
        WHERE u.emp_id = %s
    """, (emp_id,))
    user_info = cursor.fetchone()

    engine = (Config.DB_ENGINE or "mysql").lower()
    time_expr = (
        "TO_CHAR(check_in, 'HH24:MI')" if engine.startswith("post") else "TIME_FORMAT(check_in, '%%H:%%i')"
    )
    time_expr_out = (
        "TO_CHAR(check_out, 'HH24:MI')" if engine.startswith("post") else "TIME_FORMAT(check_out, '%%H:%%i')"
    )
    cursor.execute(f"""
        SELECT 
            DATE(attendance_date) AS attendance_date,
            {time_expr} AS check_in,
            {time_expr_out} AS check_out,
            status
        FROM attendance
        WHERE emp_id = %s
        ORDER BY attendance_date DESC
        LIMIT 10
    """, (emp_id,))
    attendance_records = cursor.fetchall()

    cursor.close()
    conn.close()

    if not user_info:
        flash("User data not found.", "warning")
        return redirect(url_for("login"))

    return render_template("staff/dashboard.html", user=user_info, attendance=attendance_records)

# ---------- App Entrypoint ----------
if os.getenv("FLASK_DEBUG", "0") != "1" and app.config.get("SECRET_KEY") in (None, "", "change-me-in-env", "replace-me"):
    raise RuntimeError("SECRET_KEY must be set in production")

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")
