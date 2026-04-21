"""One-off migration for the email-OTP pivot.

Non-destructive: renames otps.phone_number → otps.identifier, adds
customers.customer_email, relaxes NOT NULL on phone columns, and places a
unique index on customer_email / vendor_email. Backfills existing rows with
placeholder emails so the new NOT NULL / UNIQUE constraints can be applied
without losing records.

Re-run-safe: each step guards with information_schema so running twice is a
no-op. Kept at repo root like the other ad-hoc debug scripts.
"""
import sys
from sqlalchemy import text
from config.database import engine


STEPS = [
    # --- otps table ---------------------------------------------------------
    ("rename otps.phone_number -> otps.identifier", """
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name='otps' AND column_name='phone_number') THEN
                ALTER TABLE otps RENAME COLUMN phone_number TO identifier;
            END IF;
        END $$;
    """),
    ("widen otps.identifier to VARCHAR(255)", """
        ALTER TABLE otps ALTER COLUMN identifier TYPE VARCHAR(255);
    """),

    # --- customers table ----------------------------------------------------
    ("add customers.customer_email (nullable first)", """
        ALTER TABLE customers ADD COLUMN IF NOT EXISTS customer_email VARCHAR(255);
    """),
    ("backfill placeholder emails for existing customers", """
        UPDATE customers
           SET customer_email = 'legacy-customer-' || customer_id || '@placeholder.local'
         WHERE customer_email IS NULL;
    """),
    ("make customers.customer_email NOT NULL", """
        ALTER TABLE customers ALTER COLUMN customer_email SET NOT NULL;
    """),
    ("unique index on customers.customer_email", """
        CREATE UNIQUE INDEX IF NOT EXISTS ix_customers_customer_email
            ON customers (customer_email);
    """),
    ("relax NOT NULL on customers.customer_ph_no", """
        ALTER TABLE customers ALTER COLUMN customer_ph_no DROP NOT NULL;
    """),

    # --- vendors table ------------------------------------------------------
    ("backfill placeholder emails for existing vendors", """
        UPDATE vendors
           SET vendor_email = 'legacy-vendor-' || vendor_id || '@placeholder.local'
         WHERE vendor_email IS NULL OR vendor_email = '';
    """),
    ("make vendors.vendor_email NOT NULL", """
        ALTER TABLE vendors ALTER COLUMN vendor_email SET NOT NULL;
    """),
    # Earliest vendor_id keeps the real email; later dupes get a +dup<id> tag
    # so the unique index can be created without dropping records.
    ("dedupe vendors.vendor_email for unique index", """
        UPDATE vendors v
           SET vendor_email = regexp_replace(v.vendor_email, '@', '+dup' || v.vendor_id || '@')
         WHERE EXISTS (
             SELECT 1 FROM vendors v2
              WHERE v2.vendor_email = v.vendor_email
                AND v2.vendor_id < v.vendor_id
         );
    """),
    ("unique index on vendors.vendor_email", """
        CREATE UNIQUE INDEX IF NOT EXISTS ix_vendors_vendor_email
            ON vendors (vendor_email);
    """),
    ("relax NOT NULL on vendors.vendor_ph_no", """
        ALTER TABLE vendors ALTER COLUMN vendor_ph_no DROP NOT NULL;
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
