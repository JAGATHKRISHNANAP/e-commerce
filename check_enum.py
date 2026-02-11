
from sqlalchemy import create_engine, text
import os
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

# Get database URL from env or construct it
# Assuming standard local setup if not in env, but let's try to get it
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Fallback to defaults often used in this project context
    # DATABASE_URL = "postgresql://postgres:password@localhost/ecommerce_db"
    
    # Credentials from config/settings.py
    user = "postgres"
    password = urllib.parse.quote_plus("jaTHU@12") # Handle special chars
    server = "localhost"
    db = "e-commerce_second"
    DATABASE_URL = f"postgresql://{user}:{password}@{server}/{db}"

print(f"Connecting to: {DATABASE_URL}")

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        # Check existing values in orders table
        print("\nExisting values in orders.payment_method:")
        result = connection.execute(text("SELECT DISTINCT payment_method FROM orders"))
        for row in result:
            print(f" - {row[0]}")

        # Check enum allowed values
        print("\nAllowed values for 'paymentmethod' type:")
        # PostgreSQL specific query to get enum labels
        try:
            result = connection.execute(text("SELECT unnest(enum_range(NULL::paymentmethod))"))
            for row in result:
                print(f" - {row[0]}")
        except Exception as e:
            print(f"Could not fetch enum range (might not be a native enum?): {e}")
            
except Exception as e:
    print(f"Error: {e}")
