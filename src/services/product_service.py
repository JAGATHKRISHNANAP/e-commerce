from sqlalchemy.orm import Session
from sqlalchemy import func
from src.models.product import Product
from src.models.category import Category
from typing import Optional, Tuple, List

class ProductService:
    def __init__(self, db: Session):
        self.db = db

    def get_products_with_filters(
        self,
        page: int = 1,
        per_page: int = 20,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort_by: str = "name",
        sort_order: str = "asc"
    ) -> Tuple[List[Product], int]:
        """Get products with filtering and pagination"""
        query = self.db.query(Product)
        
        # Apply filters
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        if search:
            query = query.filter(Product.name.ilike(f"%{search}%"))
        
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        
        # Apply sorting
        if sort_order == "desc":
            query = query.order_by(getattr(Product, sort_by).desc())
        else:
            query = query.order_by(getattr(Product, sort_by).asc())
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        products = query.offset(offset).limit(per_page).all()
        
        return products, total_count

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Get a single product by ID"""
        return self.db.query(Product).filter(Product.product_id == product_id).first()

    def get_featured_products(self, limit: int = 8) -> List[Product]:
        """Get featured products"""
        return self.db.query(Product).filter(Product.stock_quantity > 0).limit(limit).all()

    def get_search_suggestions(self, query: str) -> List[str]:
        """Get search suggestions"""
        suggestions = self.db.query(Product.name).filter(
            Product.name.ilike(f"%{query}%")
        ).distinct().limit(10).all()
        
        return [suggestion[0] for suggestion in suggestions]

    def get_price_range(self, category_id: Optional[int] = None) -> dict:
        """Get price range for products"""
        query = self.db.query(Product)
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        result = query.with_entities(
            func.min(Product.price).label('min_price'),
            func.max(Product.price).label('max_price')
        ).first()
        
        return {
            "min_price": float(result.min_price) if result.min_price else 0,
            "max_price": float(result.max_price) if result.max_price else 0
        }