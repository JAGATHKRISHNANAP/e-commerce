# fresh_database_setup.py - Complete fresh setup for dynamic products
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import urllib.parse
from config.settings import settings

# URL encode the password to handle special characters
encoded_password = urllib.parse.quote_plus(settings.db_password)
DATABASE_URL = f"postgresql://{settings.db_user}:{encoded_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"

def create_fresh_database():
    """Create all tables from scratch without GIN index issues"""
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as connection:
        try:
            print("🚀 Creating fresh database with dynamic products...")
            
            # 1. Create categories table
            categories_sql = """
            CREATE TABLE IF NOT EXISTS categories (
                category_id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
            connection.execute(text(categories_sql))
            print("✅ Created categories table")
            
            # 2. Create subcategories table
            subcategories_sql = """
            CREATE TABLE IF NOT EXISTS subcategories (
                subcategory_id SERIAL PRIMARY KEY,
                category_id INTEGER NOT NULL REFERENCES categories(category_id),
                name VARCHAR(100) NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
            connection.execute(text(subcategories_sql))
            print("✅ Created subcategories table")
            
            # 3. Create specification_templates table
            spec_templates_sql = """
            CREATE TABLE IF NOT EXISTS specification_templates (
                template_id SERIAL PRIMARY KEY,
                subcategory_id INTEGER NOT NULL REFERENCES subcategories(subcategory_id),
                spec_name VARCHAR(100) NOT NULL,
                spec_type VARCHAR(50) NOT NULL CHECK (spec_type IN ('select', 'text', 'number', 'boolean')),
                spec_options JSON,
                is_required BOOLEAN DEFAULT FALSE,
                affects_price BOOLEAN DEFAULT FALSE,
                display_order INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
            connection.execute(text(spec_templates_sql))
            print("✅ Created specification_templates table")
            
            # 4. Create price_rules table
            price_rules_sql = """
            CREATE TABLE IF NOT EXISTS price_rules (
                rule_id SERIAL PRIMARY KEY,
                subcategory_id INTEGER NOT NULL REFERENCES subcategories(subcategory_id),
                specification_template_id INTEGER REFERENCES specification_templates(template_id),
                base_price INTEGER NOT NULL,
                spec_conditions JSON NOT NULL,
                price_modifier INTEGER DEFAULT 0,
                modifier_type VARCHAR(20) DEFAULT 'add' CHECK (modifier_type IN ('add', 'multiply', 'set')),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
            connection.execute(text(price_rules_sql))
            print("✅ Created price_rules table")
            
            # 5. Create products table with both old and new columns
            products_sql = """
            CREATE TABLE IF NOT EXISTS products (
                product_id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                
                -- Original pricing (for backward compatibility)
                price DECIMAL(10,2),
                
                -- New dynamic pricing
                base_price INTEGER,
                calculated_price INTEGER,
                
                -- Categories
                category_id INTEGER NOT NULL REFERENCES categories(category_id),
                subcategory_id INTEGER REFERENCES subcategories(subcategory_id),
                
                -- Dynamic specifications (JSON without GIN index)
                specifications JSON DEFAULT '{}',
                
                -- Inventory and metadata
                stock_quantity INTEGER DEFAULT 0,
                storage_capacity VARCHAR(50),
                sku VARCHAR(100) UNIQUE,
                created_by VARCHAR(100) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                
                -- Images
                primary_image_url VARCHAR(500),
                primary_image_filename VARCHAR(255),
                
                -- Timestamps
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
            connection.execute(text(products_sql))
            print("✅ Created products table")
            
            # 6. Create other essential tables for your e-commerce
            customers_sql = """
            CREATE TABLE IF NOT EXISTS customers (
                customer_id SERIAL PRIMARY KEY,
                customer_ph_no VARCHAR(20) UNIQUE NOT NULL,
                customer_name VARCHAR(255),
                date_of_registration TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
            connection.execute(text(customers_sql))
            print("✅ Created customers table")
            
            otp_sql = """
            CREATE TABLE IF NOT EXISTS otps (
                otp_id SERIAL PRIMARY KEY,
                phone_number VARCHAR(20) NOT NULL,
                otp_code VARCHAR(6) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                is_verified BOOLEAN DEFAULT FALSE
            );
            """
            connection.execute(text(otp_sql))
            print("✅ Created otps table")
            
            # 7. Create product_images table
            product_images_sql = """
            CREATE TABLE IF NOT EXISTS product_images (
                image_id SERIAL PRIMARY KEY,
                product_id INTEGER NOT NULL REFERENCES products(product_id),
                image_filename VARCHAR(255) NOT NULL,
                image_path VARCHAR(500) NOT NULL,
                image_url VARCHAR(500) NOT NULL,
                alt_text VARCHAR(255),
                is_primary BOOLEAN DEFAULT FALSE,
                display_order INTEGER DEFAULT 0,
                uploaded_by VARCHAR(100) NOT NULL,
                file_size INTEGER,
                mime_type VARCHAR(100),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
            connection.execute(text(product_images_sql))
            print("✅ Created product_images table")
            
            # 8. Create cart and order tables
            cart_sql = """
            CREATE TABLE IF NOT EXISTS carts (
                cart_id SERIAL PRIMARY KEY,
                customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
            connection.execute(text(cart_sql))
            print("✅ Created carts table")
            
            cart_items_sql = """
            CREATE TABLE IF NOT EXISTS cart_items (
                cart_item_id SERIAL PRIMARY KEY,
                cart_id INTEGER NOT NULL REFERENCES carts(cart_id),
                product_id INTEGER NOT NULL REFERENCES products(product_id),
                quantity INTEGER NOT NULL DEFAULT 1,
                added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
            connection.execute(text(cart_items_sql))
            print("✅ Created cart_items table")
            
            addresses_sql = """
            CREATE TABLE IF NOT EXISTS customer_addresses (
                address_id SERIAL PRIMARY KEY,
                customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
                address_line_1 VARCHAR(255) NOT NULL,
                address_line_2 VARCHAR(255),
                city VARCHAR(100) NOT NULL,
                state VARCHAR(100) NOT NULL,
                postal_code VARCHAR(20) NOT NULL,
                country VARCHAR(100) DEFAULT 'India',
                is_default BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
            connection.execute(text(addresses_sql))
            print("✅ Created customer_addresses table")
            
            orders_sql = """
            CREATE TABLE IF NOT EXISTS orders (
                order_id SERIAL PRIMARY KEY,
                customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
                order_status VARCHAR(50) DEFAULT 'pending',
                total_amount DECIMAL(10,2) NOT NULL,
                shipping_address_id INTEGER REFERENCES customer_addresses(address_id),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
            connection.execute(text(orders_sql))
            print("✅ Created orders table")
            
            order_items_sql = """
            CREATE TABLE IF NOT EXISTS order_items (
                order_item_id SERIAL PRIMARY KEY,
                order_id INTEGER NOT NULL REFERENCES orders(order_id),
                product_id INTEGER NOT NULL REFERENCES products(product_id),
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                total_price DECIMAL(10,2) NOT NULL
            );
            """
            connection.execute(text(order_items_sql))
            print("✅ Created order_items table")
            
            # 9. Create safe indexes (NO GIN indexes)
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_categories_name ON categories(name)",
                "CREATE INDEX IF NOT EXISTS idx_subcategories_category ON subcategories(category_id)",
                "CREATE INDEX IF NOT EXISTS idx_subcategories_name ON subcategories(name)",
                "CREATE INDEX IF NOT EXISTS idx_spec_templates_subcategory ON specification_templates(subcategory_id)",
                "CREATE INDEX IF NOT EXISTS idx_spec_templates_affects_price ON specification_templates(affects_price)",
                "CREATE INDEX IF NOT EXISTS idx_price_rules_subcategory ON price_rules(subcategory_id)",
                "CREATE INDEX IF NOT EXISTS idx_price_rules_active ON price_rules(is_active)",
                "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)",
                "CREATE INDEX IF NOT EXISTS idx_products_subcategory ON products(subcategory_id)",
                "CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)",
                "CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)",
                "CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active)",
                "CREATE INDEX IF NOT EXISTS idx_products_created_by ON products(created_by)",
                "CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(customer_ph_no)",
                "CREATE INDEX IF NOT EXISTS idx_cart_customer ON carts(customer_id)",
                "CREATE INDEX IF NOT EXISTS idx_cart_items_cart ON cart_items(cart_id)",
                "CREATE INDEX IF NOT EXISTS idx_cart_items_product ON cart_items(product_id)",
                "CREATE INDEX IF NOT EXISTS idx_addresses_customer ON customer_addresses(customer_id)",
                "CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id)",
                "CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id)"
            ]
            
            for index_sql in indexes:
                try:
                    connection.execute(text(index_sql))
                except Exception as e:
                    print(f"⚠️  Index creation: {e}")
            
            print("✅ Created all indexes (no GIN indexes)")
            
            connection.commit()
            print("🎉 Fresh database created successfully!")
            
        except Exception as e:
            print(f"❌ Database creation failed: {e}")
            connection.rollback()
            raise

def add_sample_data():
    """Add sample data for testing"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        print("\n📦 Adding sample data...")
        
        # Add sample categories
        categories_data = [
            ("Electronics", "Electronic devices and gadgets"),
            ("Clothing", "Apparel and fashion items"),
            ("Grocery", "Food and beverages"),
            ("Cosmetics", "Beauty and personal care products")
        ]
        
        for name, desc in categories_data:
            session.execute(
                text("INSERT INTO categories (name, description) VALUES (:name, :desc) ON CONFLICT (name) DO NOTHING"),
                {"name": name, "desc": desc}
            )
        
        session.commit()
        print("✅ Added sample categories")
        
        # Add sample subcategories
        subcategories_data = [
            (1, "Smartphones", "Mobile phones and accessories"),
            (1, "Laptops", "Portable computers"),
            (1, "Tablets", "Tablet devices"),
            (2, "Men's Shirts", "Shirts for men"),
            (2, "Women's Dresses", "Dresses for women"),
            (2, "Shoes", "Footwear"),
            (3, "Beverages", "Drinks and beverages"),
            (3, "Snacks", "Snack foods"),
            (4, "Skincare", "Skin care products"),
            (4, "Makeup", "Cosmetic products")
        ]
        
        for cat_id, name, desc in subcategories_data:
            session.execute(
                text("INSERT INTO subcategories (category_id, name, description) VALUES (:cat_id, :name, :desc)"),
                {"cat_id": cat_id, "name": name, "desc": desc}
            )
        
        session.commit()
        print("✅ Added sample subcategories")
        
        print("🎉 Sample data added successfully!")
        
    except Exception as e:
        print(f"❌ Error adding sample data: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("🚀 Fresh Database Setup for Dynamic E-commerce")
    print("=" * 50)
    
    # Check DATABASE_URL
    if "username:password" in DATABASE_URL:
        print("⚠️  Please set your DATABASE_URL:")
        print("   export DATABASE_URL='postgresql://user:pass@localhost/dbname'")
        print("   or edit this file directly")
        exit(1)
    
    try:
        create_fresh_database()
        add_sample_data()
        
        print("\n🎉 Fresh database setup complete!")
        print("\n📋 What was created:")
        print("✅ Categories & Subcategories")
        print("✅ Specification Templates")
        print("✅ Price Rules")
        print("✅ Dynamic Products (with JSON specs)")
        print("✅ Customer & Authentication tables")
        print("✅ Cart & Order tables")
        print("✅ Product Images")
        print("✅ All necessary indexes (NO GIN indexes)")
        
        print("\n🚀 Next steps:")
        print("1. Update your models to match the new structure")
        print("2. Run: python app.py")
        print("3. Test the API endpoints")
        print("4. Add specification templates and price rules")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check your database connection")
        print("2. Ensure PostgreSQL is running")
        print("3. Verify database credentials")
        print("4. Make sure you have CREATE permissions")