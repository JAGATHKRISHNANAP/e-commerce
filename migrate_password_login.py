"""One-off migration for the email+password login pivot.

Adds password_hash + email_verified to customers (and vendors, prepared for the
follow-up vendor pass), and adds a `purpose` column to otps so a verify-email
code cannot be replayed against a password-reset call.

Existing rows are flagged email_verified=true with password_hash=null so they
will be forced through the forgot-password flow on next login (decision 1a).

Re-run-safe: each step guards with information_schema. Kept at repo root like
the other ad-hoc migration scripts.
"""
import sys
from sqlalchemy import text
from config.database import engine


STEPS = [
    # --- otps.purpose -------------------------------------------------------
    ("add otps.purpose (default verify_email)", """
        ALTER TABLE otps
            ADD COLUMN IF NOT EXISTS purpose VARCHAR(32)
            NOT NULL DEFAULT 'verify_email';
    """),
    ("index otps.purpose", """
        CREATE INDEX IF NOT EXISTS ix_otps_purpose ON otps (purpose);
    """),

    # --- customers.password_hash + customers.email_verified -----------------
    ("add customers.password_hash (nullable)", """
        ALTER TABLE customers
            ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
    """),
    ("add customers.email_verified (default false)", """
        ALTER TABLE customers
            ADD COLUMN IF NOT EXISTS email_verified BOOLEAN
            NOT NULL DEFAULT false;
    """),
    # Decision 1a: existing OTP-only customers keep their email_verified=true
    # state but have no password yet; they must use forgot-password to set one.
    ("mark all existing customers as email_verified", """
        UPDATE customers SET email_verified = true WHERE email_verified = false;
    """),

    # --- vendors.password_hash + vendors.email_verified ---------------------
    # Added now so the same migration covers the vendor pass; the vendor auth
    # endpoints are still OTP-only until that pass lands.
    ("add vendors.password_hash (nullable)", """
        ALTER TABLE vendors
            ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
    """),
    ("add vendors.email_verified (default false)", """
        ALTER TABLE vendors
            ADD COLUMN IF NOT EXISTS email_verified BOOLEAN
            NOT NULL DEFAULT false;
    """),
    ("mark all existing vendors as email_verified", """
        UPDATE vendors SET email_verified = true WHERE email_verified = false;
    """),
]


def main():
    with engine.begin() as conn:
        for label, sql in STEPS:
            print(f"[migrate] {label} ...", end=" ", flush=True)
            try:
                conn.execute(text(sql))
                print("ok")
            except Exception as exc:
                print(f"FAILED: {exc}")
                raise
    print("[migrate] done.")


if __name__ == "__main__":
    sys.exit(main())
