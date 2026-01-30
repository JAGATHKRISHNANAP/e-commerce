
from config.database import SessionLocal
# Import all models to ensure mappers are initialized
from src.models.product import Product
from src.models.vendor import Vendor
from src.models.order import Order, OrderItem
from src.models.customer import Customer
from src.models.category import Category, Subcategory
from src.models.cart import Cart, CartItem
from src.models.address import CustomerAddress

db = SessionLocal()

vendor_phone = "+919495406368"
print(f"Updating products to be owned by: {vendor_phone}")

try:
    products = db.query(Product).all()
    count = 0
    for p in products:
        # Update 'admin' or NULL products to be owned by this vendor for testing
        if p.created_by == 'admin' or p.created_by is None:
            print(f"Updating Product: {p.name} (ID: {p.product_id}) - Old Owner: {p.created_by}")
            p.created_by = vendor_phone
            count += 1

    if count > 0:
        db.commit()
        print(f"\nSuccessfully updated {count} products.")
    else:
        print("\nNo products needed updating.")

except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
