
from sqlalchemy import create_engine, text
import urllib.parse

# Credentials from config/settings.py
user = "postgres"
password = urllib.parse.quote_plus("jaTHU@12")
server = "localhost"
db = "e-commerce_second"
DATABASE_URL = f"postgresql://{user}:{password}@{server}/{db}"

print(f"Connecting to: {DATABASE_URL}")

try:
    engine = create_engine(DATABASE_URL)
    # Use execution_options to enable autocommit for ALTER TYPE
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        print("Attempting to add 'RAZORPAY' to 'paymentmethod' enum...")
        try:
            connection.execute(text("ALTER TYPE paymentmethod ADD VALUE 'RAZORPAY'"))
            print("Successfully added 'RAZORPAY'.")
        except Exception as e:
            print(f"Error adding RAZORPAY (might already exist): {e}")

        # Just in case, try adding lowercase 'razorpay' too if the DB is messy, 
        # but the error specifically said "RAZORPAY" was invalid.
        # Postgres might throw error if we try to add what exists, so we wrap in try/except.
        # print("Attempting to add 'razorpay' (lowercase) just in case...")
        # try:
        #     connection.execute(text("ALTER TYPE paymentmethod ADD VALUE 'razorpay'"))
        #     print("Successfully added 'razorpay'.")
        # except Exception as e:
        #     print(f"Error adding razorpay: {e}")

except Exception as e:
    print(f"Connection Error: {e}")
