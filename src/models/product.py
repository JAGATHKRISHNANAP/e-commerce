# src/models/product.py - Updated with Elasticsearch integration
from sqlalchemy import Column, Integer, String, Text, DECIMAL, ForeignKey, JSON, Boolean, DateTime, event
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base
import logging

logger = logging.getLogger(__name__)

class Product(Base):
    __tablename__ = "products"
    
    product_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Original pricing (keep for backward compatibility)
    price = Column(DECIMAL(10, 2), nullable=True)
    
    # New dynamic pricing
    base_price = Column(Integer, nullable=True)  # Base price in cents
    calculated_price = Column(Integer, nullable=True)  # Final calculated price in cents
    
    # Categories
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
    subcategory_id = Column(Integer, ForeignKey("subcategories.subcategory_id"), nullable=True)
    
    # Dynamic specifications - JSON column (NO GIN INDEX)
    specifications = Column(JSON, nullable=False, default={})
    
    # Inventory and metadata
    stock_quantity = Column(Integer, default=0)
    storage_capacity = Column(String(50))  # Keep for backward compatibility
    sku = Column(String(100), unique=True, nullable=True, index=True)
    group_id = Column(String(100), index=True, nullable=True)  # Links variants together
    created_by = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Image fields
    primary_image_url = Column(String(500), nullable=True)
    primary_image_filename = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    category = relationship("Category", back_populates="products")
    subcategory = relationship("Subcategory", back_populates="products")
    cart_items = relationship("CartItem", back_populates="product")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")


# ===================================================================
# ELASTICSEARCH AUTO-INDEXING EVENT LISTENERS
# ===================================================================

def auto_index_product(product_id: int):
    """Automatically index a product when it's created/updated"""
    try:
        # Import here to avoid circular imports
        from src.services.search import ElasticsearchService
        from config.database import SessionLocal
        
        db = SessionLocal()
        try:
            product = db.query(Product).filter(Product.product_id == product_id).first()
            
            if product:
                if product.is_active:
                    ElasticsearchService.index_product(product)
                    logger.info(f"Auto-indexed product {product_id}")
                else:
                    ElasticsearchService.delete_product(product_id)
                    logger.info(f"Removed inactive product {product_id} from index")
            
        except Exception as e:
            logger.error(f"Auto-indexing failed for product {product_id}: {str(e)}")
        finally:
            db.close()
            
    except ImportError:
        # Elasticsearch service not available, skip indexing
        logger.debug(f"Elasticsearch service not available, skipping auto-indexing for product {product_id}")
    except Exception as e:
        logger.error(f"Auto-indexing error for product {product_id}: {str(e)}")


def auto_remove_product(product_id: int):
    """Automatically remove a product from index when deleted"""
    try:
        # Import here to avoid circular imports
        from src.services.search import ElasticsearchService
        
        ElasticsearchService.delete_product(product_id)
        logger.info(f"Auto-removed product {product_id} from index")
        
    except ImportError:
        # Elasticsearch service not available, skip removal
        logger.debug(f"Elasticsearch service not available, skipping auto-removal for product {product_id}")
    except Exception as e:
        logger.error(f"Auto-removal failed for product {product_id}: {str(e)}")


# Event listeners for automatic Elasticsearch indexing
@event.listens_for(Product, 'after_insert')
def auto_index_on_insert(mapper, connection, target):
    """Auto-index product after creation"""
    try:
        # Use a background task or queue for production
        auto_index_product(target.product_id)
    except Exception as e:
        logger.error(f"Auto-indexing after insert failed: {str(e)}")


@event.listens_for(Product, 'after_update')
def auto_index_on_update(mapper, connection, target):
    """Auto-index product after update"""
    try:
        # Use a background task or queue for production
        auto_index_product(target.product_id)
    except Exception as e:
        logger.error(f"Auto-indexing after update failed: {str(e)}")


@event.listens_for(Product, 'before_delete')
def auto_remove_on_delete(mapper, connection, target):
    """Auto-remove product before deletion"""
    try:
        # Use a background task or queue for production
        auto_remove_product(target.product_id)
    except Exception as e:
        logger.error(f"Auto-removal before delete failed: {str(e)}")


# ===================================================================
# PRODUCT UTILITY METHODS
# ===================================================================

class ProductUtils:
    """Utility methods for product operations"""
    
    @staticmethod
    def get_effective_price(product: Product) -> float:
        """Get the effective price for a product"""
        if product.calculated_price is not None:
            return product.calculated_price / 100  # Convert cents to dollars
        elif product.base_price is not None:
            return product.base_price / 100  # Convert cents to dollars
        elif product.price is not None:
            return float(product.price)
        else:
            return 0.0
    
    @staticmethod
    def format_price(product: Product) -> str:
        """Format product price for display"""
        price = ProductUtils.get_effective_price(product)
        return f"${price:.2f}"
    
    @staticmethod
    def is_in_stock(product: Product) -> bool:
        """Check if product is in stock"""
        return product.stock_quantity > 0 if product.stock_quantity else False
    
    @staticmethod
    def get_stock_status(product: Product) -> str:
        """Get human-readable stock status"""
        if not product.stock_quantity or product.stock_quantity <= 0:
            return "Out of Stock"
        elif product.stock_quantity <= 5:
            return f"Low Stock ({product.stock_quantity} left)"
        else:
            return f"In Stock ({product.stock_quantity} available)"
    
    @staticmethod
    def extract_brand(product: Product) -> str:
        """Extract brand from product specifications or name"""
        if product.specifications and isinstance(product.specifications, dict):
            brand = product.specifications.get('Brand') or product.specifications.get('brand')
            if brand:
                return brand
        
        # Try to extract brand from product name (first word)
        if product.name:
            words = product.name.split()
            if words:
                return words[0]
        
        return "Unknown"
    
    @staticmethod
    def get_search_keywords(product: Product) -> list:
        """Generate search keywords for the product"""
        keywords = []
        
        if product.name:
            keywords.extend(product.name.lower().split())
        
        if product.description:
            # Get first few words from description
            desc_words = product.description.lower().split()[:10]
            keywords.extend(desc_words)
        
        if product.category and hasattr(product.category, 'name'):
            keywords.extend(product.category.name.lower().split())
        
        if product.subcategory and hasattr(product.subcategory, 'name'):
            keywords.extend(product.subcategory.name.lower().split())
        
        # Extract from specifications
        if product.specifications and isinstance(product.specifications, dict):
            for key, value in product.specifications.items():
                if isinstance(value, str):
                    keywords.extend(value.lower().split())
        
        # Remove duplicates and return
        return list(set(keywords))


# ===================================================================
# ELASTICSEARCH REINDEXING COMMANDS
# ===================================================================

def reindex_all_products():
    """
    Utility function to reindex all products
    Can be called from management commands or admin interface
    """
    try:
        from src.services.search import ElasticsearchService
        from config.database import SessionLocal
        
        db = SessionLocal()
        try:
            products = db.query(Product).filter(Product.is_active == True).all()
            result = ElasticsearchService.bulk_index_products(products)
            logger.info(f"Reindexed {len(products)} products: {result}")
            return result
        finally:
            db.close()
            
    except ImportError:
        logger.error("Elasticsearch service not available")
        return {"error": "Elasticsearch service not available"}
    except Exception as e:
        logger.error(f"Reindexing failed: {str(e)}")
        return {"error": str(e)}


def index_single_product_by_id(product_id: int):
    """
    Utility function to index a single product by ID
    """
    try:
        from src.services.search import ElasticsearchService
        from config.database import SessionLocal
        
        db = SessionLocal()
        try:
            product = db.query(Product).filter(Product.product_id == product_id).first()
            if product:
                success = ElasticsearchService.index_product(product)
                logger.info(f"Indexed product {product_id}: {success}")
                return {"success": success, "product_id": product_id}
            else:
                logger.warning(f"Product {product_id} not found")
                return {"error": f"Product {product_id} not found"}
        finally:
            db.close()
            
    except ImportError:
        logger.error("Elasticsearch service not available")
        return {"error": "Elasticsearch service not available"}
    except Exception as e:
        logger.error(f"Indexing failed for product {product_id}: {str(e)}")
        return {"error": str(e)}


# ===================================================================
# USAGE EXAMPLES
# ===================================================================

"""
# Example usage of utility methods:

# Get effective price
product = db.query(Product).first()
price = ProductUtils.get_effective_price(product)

# Format price for display
formatted_price = ProductUtils.format_price(product)

# Check stock status
is_available = ProductUtils.is_in_stock(product)
stock_status = ProductUtils.get_stock_status(product)

# Get brand
brand = ProductUtils.extract_brand(product)

# Reindex all products (for admin/management)
result = reindex_all_products()

# Index single product
result = index_single_product_by_id(123)
"""