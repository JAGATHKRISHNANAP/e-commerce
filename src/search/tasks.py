# src/search/tasks.py - Background tasks for automatic indexing
from config.database import get_db
from src.services.search import ElasticsearchService
from src.models.product import Product
import logging

logger = logging.getLogger(__name__)

class SearchTasks:
    """Background tasks for search index management"""
    
    @staticmethod
    def auto_index_product(product_id: int):
        """Automatically index a product when it's created/updated"""
        try:
            db = next(get_db())
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
    
    @staticmethod
    def auto_remove_product(product_id: int):
        """Automatically remove a product from index when deleted"""
        try:
            ElasticsearchService.delete_product(product_id)
            logger.info(f"Auto-removed product {product_id} from index")
            
        except Exception as e:
            logger.error(f"Auto-removal failed for product {product_id}: {str(e)}")