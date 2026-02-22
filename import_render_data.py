import argparse
from pathlib import Path
import time

import psycopg2
from werkzeug.security import generate_password_hash


def run(db_url: str, data_dir: Path, sslmode: str = "require") -> None:
    files = [
        data_dir / "employees.sql",
        data_dir / "attendance.sql",
        data_dir / "salaries.sql",
    ]
    for file_path in files:
        if not file_path.exists():
            raise FileNotFoundError(f"Missing file: {file_path}")

    conn = psycopg2.connect(db_url, sslmode=sslmode)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
          emp_id SERIAL PRIMARY KEY,
          first_name VARCHAR(100),
          last_name VARCHAR(100),
          email VARCHAR(150),
          phone VARCHAR(30),
          department VARCHAR(100),
          role VARCHAR(20) NOT NULL DEFAULT 'staff',
          status VARCHAR(20) NOT NULL DEFAULT 'active'
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
          user_id SERIAL PRIMARY KEY,
          emp_id INT NOT NULL REFERENCES employees(emp_id) ON DELETE CASCADE,
          username VARCHAR(100) UNIQUE NOT NULL,
          password_hash TEXT NOT NULL,
          role VARCHAR(20) NOT NULL DEFAULT 'staff'
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance (
          attendance_id SERIAL PRIMARY KEY,
          emp_id INT NOT NULL REFERENCES employees(emp_id) ON DELETE CASCADE,
          attendance_date DATE NOT NULL,
          check_in TIME NULL,
          check_out TIME NULL,
          status VARCHAR(20) NOT NULL DEFAULT 'present'
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS salaries (
          salary_id SERIAL PRIMARY KEY,
          emp_id INT NOT NULL REFERENCES employees(emp_id) ON DELETE CASCADE,
          month INT NULL,
          base_salary NUMERIC(12,2) NOT NULL DEFAULT 0,
          bonus NUMERIC(12,2) NOT NULL DEFAULT 0,
          deductions NUMERIC(12,2) NOT NULL DEFAULT 0,
          paid_status VARCHAR(20) NOT NULL DEFAULT 'unpaid',
          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    # Backfill schema when salaries table already exists from older setup.
    cur.execute("ALTER TABLE salaries ADD COLUMN IF NOT EXISTS month INT NULL")
    conn.commit()

    # Render web service may read these tables while import runs.
    # Retry truncate on deadlock/lock-timeout until locks become available.
    for attempt in range(1, 9):
        try:
            cur.execute("SET lock_timeout TO '5s'")
            cur.execute("TRUNCATE TABLE users, attendance, salaries, employees RESTART IDENTITY CASCADE")
            conn.commit()
            break
        except psycopg2.Error as e:
            conn.rollback()
            code = getattr(e, "pgcode", "")
            if code not in ("40P01", "55P03") or attempt == 8:
                raise
            wait_s = attempt * 2
            print(f"Lock conflict during truncate, retrying in {wait_s}s (attempt {attempt}/8)")
            time.sleep(wait_s)

    for file_path in files:
        count = 0
        with file_path.open("r", encoding="utf-8") as f:
            for line in f:
                stmt = line.strip()
                if not stmt:
                    continue
                cur.execute(stmt)
                count += 1
        conn.commit()
        print(f"Loaded {count} rows from {file_path.name}")

    cur.execute(
        "SELECT emp_id FROM employees WHERE LOWER(role)='admin' AND LOWER(status)='active' ORDER BY emp_id LIMIT 1"
    )
    admin_emp_id = cur.fetchone()[0]

    cur.execute(
        "SELECT emp_id FROM employees WHERE LOWER(role)='staff' AND LOWER(status)='active' ORDER BY emp_id LIMIT 1"
    )
    employee_emp_id = cur.fetchone()[0]

    admin_hash = generate_password_hash("admin123")
    employee_hash = generate_password_hash("employee123")

    cur.execute(
        """
        INSERT INTO users (emp_id, username, password_hash, role)
        VALUES (%s, 'admin', %s, 'admin')
        ON CONFLICT (username) DO UPDATE
        SET emp_id = EXCLUDED.emp_id,
            password_hash = EXCLUDED.password_hash,
            role = EXCLUDED.role
        """,
        (admin_emp_id, admin_hash),
    )
    cur.execute(
        """
        INSERT INTO users (emp_id, username, password_hash, role)
        VALUES (%s, 'employee', %s, 'staff')
        ON CONFLICT (username) DO UPDATE
        SET emp_id = EXCLUDED.emp_id,
            password_hash = EXCLUDED.password_hash,
            role = EXCLUDED.role
        """,
        (employee_emp_id, employee_hash),
    )
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM employees")
    emp_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM attendance")
    attendance_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM salaries")
    salaries_count = cur.fetchone()[0]

    print(f"admin mapped to emp_id={admin_emp_id}")
    print(f"employee mapped to emp_id={employee_emp_id}")
    print(f"employees={emp_count}, attendance={attendance_count}, salaries={salaries_count}")
    print("Import complete")

    cur.close()
    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-url", required=True, help="Render External Database URL")
    parser.add_argument("--data-dir", default=r"C:\Users\khan\Desktop\data")
    parser.add_argument("--sslmode", default="require")
    args = parser.parse_args()

    run(args.db_url, Path(args.data_dir), args.sslmode)


if __name__ == "__main__":
    main()
