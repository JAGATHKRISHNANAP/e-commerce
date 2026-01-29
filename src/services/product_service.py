# from sqlalchemy.orm import Session
# from sqlalchemy import func
# from src.models.product import Product
# from src.models.category import Category
# from typing import Optional, Tuple, List

# class ProductService:
#     def __init__(self, db: Session):
#         self.db = db

#     def get_products_with_filters(
#         self,
#         page: int = 1,
#         per_page: int = 20,
#         category_id: Optional[int] = None,
#         search: Optional[str] = None,
#         min_price: Optional[float] = None,
#         max_price: Optional[float] = None,
#         sort_by: str = "name",
#         sort_order: str = "asc"
#     ) -> Tuple[List[Product], int]:
#         """Get products with filtering and pagination"""
#         query = self.db.query(Product)
        
#         # Apply filters
#         if category_id:
#             query = query.filter(Product.category_id == category_id)
        
#         if search:
#             query = query.filter(Product.name.ilike(f"%{search}%"))
        
#         if min_price is not None:
#             query = query.filter(Product.price >= min_price)
        
#         if max_price is not None:
#             query = query.filter(Product.price <= max_price)
        
#         # Apply sorting
#         if sort_order == "desc":
#             query = query.order_by(getattr(Product, sort_by).desc())
#         else:
#             query = query.order_by(getattr(Product, sort_by).asc())
        
#         # Get total count
#         total_count = query.count()
        
#         # Apply pagination
#         offset = (page - 1) * per_page
#         products = query.offset(offset).limit(per_page).all()
        
#         return products, total_count

#     def get_product_by_id(self, product_id: int) -> Optional[Product]:
#         """Get a single product by ID"""
#         return self.db.query(Product).filter(Product.product_id == product_id).first()

#     def get_featured_products(self, limit: int = 8) -> List[Product]:
#         """Get featured products"""
#         return self.db.query(Product).filter(Product.stock_quantity > 0).limit(limit).all()

#     def get_search_suggestions(self, query: str) -> List[str]:
#         """Get search suggestions"""
#         suggestions = self.db.query(Product.name).filter(
#             Product.name.ilike(f"%{query}%")
#         ).distinct().limit(10).all()
        
#         return [suggestion[0] for suggestion in suggestions]

#     def get_price_range(self, category_id: Optional[int] = None) -> dict:
#         """Get price range for products"""
#         query = self.db.query(Product)
        
#         if category_id:
#             query = query.filter(Product.category_id == category_id)
        
#         result = query.with_entities(
#             func.min(Product.price).label('min_price'),
#             func.max(Product.price).label('max_price')
#         ).first()
        
#         return {
#             "min_price": float(result.min_price) if result.min_price else 0,
#             "max_price": float(result.max_price) if result.max_price else 0
#         }





from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from src.models.product import Product
from src.models.category import Category
from typing import Optional, Tuple, List
from src.schemas.product import ProductResponse  # Add this import

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

    # def get_product_by_id(self, product_id: int) -> Optional[ProductResponse]:
    #     """Get a single product by ID and return as ProductResponse"""
    #     # Query with joined relationships
    #     product = self.db.query(Product).options(
    #         joinedload(Product.category),
    #         joinedload(Product.subcategory),
    #         joinedload(Product.images)
    #     ).filter(Product.product_id == product_id).first()
        
    #     if not product:
    #         return None
        
    #     # Convert to response format
    #     response_data = {
    #         "product_id": product.product_id,
    #         "name": product.name,
    #         "description": product.description,
    #         "category_id": product.category_id,
    #         "subcategory_id": product.subcategory_id,
    #         "specifications": product.specifications,
    #         "base_price": product.base_price,
    #         "calculated_price": product.calculated_price,
    #         "stock_quantity": product.stock_quantity,
    #         "sku": product.sku,
    #         "is_active": product.is_active,
    #         "created_by": product.created_by,
    #         "created_at": product.created_at,
    #         "updated_at": product.updated_at,
    #         "category": {
    #             "category_id": product.category.category_id,
    #             "name": product.category.name,
    #             "description": product.category.description
    #         } if product.category else None,
    #         "subcategory": {
    #             "subcategory_id": product.subcategory.subcategory_id,
    #             "name": product.subcategory.name,
    #             "description": product.subcategory.description
    #         } if product.subcategory else None,
    #         "primary_image_url": product.primary_image_url,
    #         "primary_image_filename": product.primary_image_filename
    #     }
        
    #     return ProductResponse(**response_data)

    def get_product_by_id(self, product_id: int) -> Optional[ProductResponse]:
        """Get a single product by ID and return as ProductResponse"""
        # Query with joined relationships
        product = self.db.query(Product).options(
            joinedload(Product.category),
            joinedload(Product.subcategory),
            joinedload(Product.images)
        ).filter(Product.product_id == product_id).first()
        
        if not product:
            return None
        
        # Fetch variants (siblings with same group_id)
        variants = []
        if product.group_id:
            variant_products = self.db.query(Product).filter(
                Product.group_id == product.group_id,
                Product.product_id != product.product_id,
                Product.is_active == True
            ).all()
            
            for vp in variant_products:
                variants.append({
                    "product_id": vp.product_id,
                    "name": vp.name,
                    "specifications": vp.specifications,
                    "base_price": vp.base_price,
                    "calculated_price": vp.calculated_price,
                    "stock_quantity": vp.stock_quantity,
                    "primary_image_url": vp.primary_image_url,
                    # Add any other needed fields for the switcher
                })

        # Convert to response format
        response_data = {
            "product_id": product.product_id,
            "name": product.name,
            "description": product.description,
            "category_id": product.category_id,
            "subcategory_id": product.subcategory_id,
            "specifications": product.specifications,
            "base_price": product.base_price,
            "calculated_price": product.calculated_price,
            "stock_quantity": product.stock_quantity,
            "sku": product.sku,
            "group_id": product.group_id,  # Add group_id
            "is_active": product.is_active,
            "created_by": product.created_by,
            "created_at": product.created_at,
            "updated_at": product.updated_at,
            "category": {
                "category_id": product.category.category_id,
                "name": product.category.name,
                "description": product.category.description
            } if product.category else None,
            "subcategory": {
                "subcategory_id": product.subcategory.subcategory_id,
                "name": product.subcategory.name,
                "description": product.subcategory.description
            } if product.subcategory else None,
            "primary_image_url": product.primary_image_url,
            "primary_image_filename": product.primary_image_filename,
            # ADD THIS LINE - Convert images to response format
            "images": [
                {
                    "image_id": img.image_id,
                    "product_id": img.product_id,
                    "image_filename": img.image_filename,
                    "image_url": img.image_url,
                    "image_path": img.image_path,
                    "alt_text": img.alt_text,
                    "is_primary": img.is_primary,
                    "display_order": img.display_order,
                    "uploaded_by": img.uploaded_by,
                    "file_size": img.file_size,
                    "mime_type": img.mime_type,
                    "created_at": img.created_at,
                    "updated_at": img.updated_at
                }
                for img in product.images
            ] if product.images else [],
            "variants": variants
        }
        
        return ProductResponse(**response_data)



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