
from config.database import SessionLocal
from src.models.product import Product
from src.models.vendor import Vendor
from src.models.order import Order, OrderItem
from src.models.customer import Customer

db = SessionLocal()

print("--- debug_orders.py ---")

# 1. List all Vendors
vendors = db.query(Vendor).all()
print(f"\nFound {len(vendors)} Vendors:")
for v in vendors:
    print(f"  ID: {v.vendor_id}, Phone: {v.vendor_ph_no}, Name: {v.vendor_name}")

# 2. List all Products and their 'created_by'
products = db.query(Product).all()
print(f"\nFound {len(products)} Products:")
for p in products:
    print(f"  ID: {p.product_id}, Name: {p.name}, Created By: '{p.created_by}'")

# 3. List all Orders and Items
orders = db.query(Order).all()
print(f"\nFound {len(orders)} Orders:")
for o in orders:
    print(f"  Order ID: {o.order_id}, Status: {o.order_status}")
    for item in o.order_items:
        product = db.query(Product).filter(Product.product_id == item.product_id).first()
        created_by = product.created_by if product else "UNKNOWN"
        print(f"    - Item: {item.product_name} (Prod ID: {item.product_id}), Product Created By: '{created_by}'")

print("\n--- End Debug ---")
db.close()
