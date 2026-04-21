"""One-off migration to add products.discount_percent.

Non-destructive: adds a single nullable-free INT column with default 0,
so existing rows read as "no discount" without any data change.

Re-run-safe: guarded with IF NOT EXISTS / information_schema — rerunning
is a no-op.
"""
import sys
from sqlalchemy import text
from config.database import engine


STEPS = [
    ("add products.discount_percent column", """
        ALTER TABLE products
          ADD COLUMN IF NOT EXISTS discount_percent INTEGER NOT NULL DEFAULT 0;
    """),
    ("sanity-check: clamp any out-of-range values to [0, 100]", """
        UPDATE products
           SET discount_percent = LEAST(100, GREATEST(0, discount_percent))
         WHERE discount_percent < 0 OR discount_percent > 100;
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
