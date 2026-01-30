
from config.database import SessionLocal
from src.models.product import Product

db = SessionLocal()

print("--- Checking Product Image URLs ---")
products = db.query(Product).filter(Product.created_by == '+919495406368').all()

for p in products:
    print(f"ID: {p.product_id}, Name: {p.name}, Image URL: '{p.primary_image_url}', Filename: '{p.primary_image_filename}'")

print("--- End Check ---")
db.close()
