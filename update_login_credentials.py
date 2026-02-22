import argparse

import psycopg2
from werkzeug.security import generate_password_hash


def main() -> None:
    parser = argparse.ArgumentParser(description="Update admin/staff login credentials")
    parser.add_argument("--db-url", required=True, help="Render External Database URL")
    parser.add_argument("--admin-user", default="admin")
    parser.add_argument("--admin-pass", required=True)
    parser.add_argument("--staff-user", default="employee")
    parser.add_argument("--staff-pass", required=True)
    parser.add_argument("--sslmode", default="require")
    args = parser.parse_args()

    conn = psycopg2.connect(args.db_url, sslmode=args.sslmode)
    cur = conn.cursor()

    admin_hash = generate_password_hash(args.admin_pass)
    staff_hash = generate_password_hash(args.staff_pass)

    cur.execute(
        "UPDATE users SET password_hash=%s, role='admin' WHERE username=%s",
        (admin_hash, args.admin_user),
    )
    admin_updated = cur.rowcount

    cur.execute(
        "UPDATE users SET password_hash=%s, role='staff' WHERE username=%s",
        (staff_hash, args.staff_user),
    )
    staff_updated = cur.rowcount

    conn.commit()
    cur.close()
    conn.close()

    print(f"admin updated rows: {admin_updated}")
    print(f"staff updated rows: {staff_updated}")
    print("Credential update complete")


if __name__ == "__main__":
    main()
