# # # src/services/search.py
# # from typing import List, Dict, Any, Optional
# # from elasticsearch_dsl import Search, Q
# # from elasticsearch.helpers import bulk
# # from src.documents.search import ProductDocument
# # from src.models.product import Product
# # from config.elasticsearch import es_client
# # import logging

# # logger = logging.getLogger(__name__)

# # class ElasticsearchService:
    
# #     @staticmethod
# #     def initialize_index():
# #         """Initialize the Elasticsearch index"""
# #         try:
# #             ProductDocument.init()
# #             logger.info("Elasticsearch index initialized successfully")
# #         except Exception as e:
# #             logger.error(f"Failed to initialize Elasticsearch index: {str(e)}")
# #             raise
    
# #     @staticmethod
# #     def index_product(product: Product) -> bool:
# #         """Index a single product"""
# #         try:
# #             # Get effective price
# #             effective_price = None
# #             if product.calculated_price is not None:
# #                 effective_price = product.calculated_price / 100
# #             elif product.base_price is not None:
# #                 effective_price = product.base_price / 100
# #             elif product.price is not None:
# #                 effective_price = float(product.price)
            
# #             # Create search keywords from various fields
# #             search_keywords = []
# #             if product.name:
# #                 search_keywords.append(product.name)
# #             if product.description:
# #                 search_keywords.append(product.description)
# #             if product.category and product.category.name:
# #                 search_keywords.append(product.category.name)
# #             if product.subcategory and product.subcategory.name:
# #                 search_keywords.append(product.subcategory.name)
            
# #             # Extract brand from specifications or name
# #             brand = None
# #             if product.specifications and isinstance(product.specifications, dict):
# #                 brand = product.specifications.get('Brand') or product.specifications.get('brand')
            
# #             # Create document
# #             doc = ProductDocument(
# #                 meta={'id': product.product_id},
# #                 product_id=product.product_id,
# #                 name=product.name,
# #                 description=product.description,
# #                 price=effective_price,
# #                 base_price=product.base_price,
# #                 calculated_price=product.calculated_price,
# #                 category_id=product.category_id,
# #                 category_name=product.category.name if product.category else None,
# #                 subcategory_id=product.subcategory_id,
# #                 subcategory_name=product.subcategory.name if product.subcategory else None,
# #                 brand=brand,
# #                 sku=product.sku,
# #                 stock_quantity=product.stock_quantity,
# #                 storage_capacity=product.storage_capacity,
# #                 specifications=str(product.specifications) if product.specifications else "",
# #                 primary_image_url=product.primary_image_url,
# #                 search_keywords=' '.join(search_keywords),
# #                 popularity_score=1.0,  # Default, can be calculated based on sales/views
# #                 is_active=product.is_active,
# #                 created_at=product.created_at,
# #                 updated_at=product.updated_at
# #             )
            
# #             doc.save()
# #             logger.info(f"Product {product.product_id} indexed successfully")
# #             return True
            
# #         except Exception as e:
# #             logger.error(f"Failed to index product {product.product_id}: {str(e)}")
# #             return False
    
# #     @staticmethod
# #     def bulk_index_products(products: List[Product]) -> Dict[str, int]:
# #         """Bulk index multiple products"""
# #         success_count = 0
# #         error_count = 0
        
# #         def generate_docs():
# #             for product in products:
# #                 try:
# #                     # Get effective price
# #                     effective_price = None
# #                     if product.calculated_price is not None:
# #                         effective_price = product.calculated_price / 100
# #                     elif product.base_price is not None:
# #                         effective_price = product.base_price / 100
# #                     elif product.price is not None:
# #                         effective_price = float(product.price)
                    
# #                     # Create search keywords
# #                     search_keywords = []
# #                     if product.name:
# #                         search_keywords.append(product.name)
# #                     if product.description:
# #                         search_keywords.append(product.description)
# #                     if product.category and product.category.name:
# #                         search_keywords.append(product.category.name)
                    
# #                     # Extract brand
# #                     brand = None
# #                     if product.specifications and isinstance(product.specifications, dict):
# #                         brand = product.specifications.get('Brand') or product.specifications.get('brand')
                    
# #                     yield {
# #                         '_index': 'ecommerce_products',
# #                         '_id': product.product_id,
# #                         '_source': {
# #                             'product_id': product.product_id,
# #                             'name': product.name,
# #                             'description': product.description,
# #                             'price': effective_price,
# #                             'base_price': product.base_price,
# #                             'calculated_price': product.calculated_price,
# #                             'category_id': product.category_id,
# #                             'category_name': product.category.name if product.category else None,
# #                             'subcategory_id': product.subcategory_id,
# #                             'subcategory_name': product.subcategory.name if product.subcategory else None,
# #                             'brand': brand,
# #                             'sku': product.sku,
# #                             'stock_quantity': product.stock_quantity,
# #                             'storage_capacity': product.storage_capacity,
# #                             'specifications': str(product.specifications) if product.specifications else "",
# #                             'primary_image_url': product.primary_image_url,
# #                             'search_keywords': ' '.join(search_keywords),
# #                             'popularity_score': 1.0,
# #                             'is_active': product.is_active,
# #                             'created_at': product.created_at,
# #                             'updated_at': product.updated_at
# #                         }
# #                     }
# #                 except Exception as e:
# #                     logger.error(f"Error preparing product {product.product_id} for indexing: {str(e)}")
# #                     continue
        
# #         try:
# #             success, failed = bulk(es_client, generate_docs())
# #             success_count = success
# #             error_count = len(failed)
            
# #             logger.info(f"Bulk indexing completed: {success_count} success, {error_count} errors")
            
# #         except Exception as e:
# #             logger.error(f"Bulk indexing failed: {str(e)}")
# #             error_count = len(products)
        
# #         return {
# #             'success': success_count,
# #             'errors': error_count,
# #             'total': len(products)
# #         }
    
# #     @staticmethod
# #     def search_products(
# #         query: str,
# #         category_id: Optional[int] = None,
# #         subcategory_id: Optional[int] = None,
# #         min_price: Optional[float] = None,
# #         max_price: Optional[float] = None,
# #         brand: Optional[str] = None,
# #         in_stock_only: bool = True,
# #         sort_by: str = 'relevance',
# #         page: int = 1,
# #         size: int = 20
# #     ) -> Dict[str, Any]:
# #         """Advanced product search with filters"""
        
# #         search = Search(using=es_client, index='ecommerce_products')
        
# #         # Base query - multi-field search
# #         if query:
# #             search_query = Q('multi_match', 
# #                            query=query,
# #                            fields=[
# #                                'name^3',  # Boost name matches
# #                                'name.autocomplete^2',
# #                                'description',
# #                                'category_name.text',
# #                                'subcategory_name.text',
# #                                'brand.text',
# #                                'search_keywords',
# #                                'specifications'
# #                            ],
# #                            fuzziness='AUTO',
# #                            operator='and')
# #         else:
# #             search_query = Q('match_all')
        
# #         # Apply filters
# #         filters = []
        
# #         # Active products only
# #         filters.append(Q('term', is_active=True))
        
# #         # Stock filter
# #         if in_stock_only:
# #             filters.append(Q('range', stock_quantity={'gt': 0}))
        
# #         # Category filter
# #         if category_id:
# #             filters.append(Q('term', category_id=category_id))
        
# #         # Subcategory filter
# #         if subcategory_id:
# #             filters.append(Q('term', subcategory_id=subcategory_id))
        
# #         # Price range filter
# #         if min_price is not None or max_price is not None:
# #             price_range = {}
# #             if min_price is not None:
# #                 price_range['gte'] = min_price
# #             if max_price is not None:
# #                 price_range['lte'] = max_price
# #             filters.append(Q('range', price=price_range))
        
# #         # Brand filter
# #         if brand:
# #             filters.append(Q('term', brand=brand))
        
# #         # Combine query and filters
# #         if filters:
# #             search = search.query(Q('bool', must=[search_query], filter=filters))
# #         else:
# #             search = search.query(search_query)
        
# #         # Sorting
# #         if sort_by == 'price_low':
# #             search = search.sort('price')
# #         elif sort_by == 'price_high':
# #             search = search.sort('-price')
# #         elif sort_by == 'newest':
# #             search = search.sort('-created_at')
# #         elif sort_by == 'popularity':
# #             search = search.sort('-popularity_score', '_score')
# #         else:  # relevance (default)
# #             search = search.sort('_score')
        
# #         # Pagination
# #         start = (page - 1) * size
# #         search = search[start:start + size]
        
# #         # Add aggregations for facets
# #         search.aggs.bucket('categories', 'terms', field='category_name', size=10)
# #         search.aggs.bucket('brands', 'terms', field='brand', size=10)
# #         search.aggs.bucket('price_ranges', 'range', field='price', ranges=[
# #             {'from': 0, 'to': 50, 'key': '0-50'},
# #             {'from': 50, 'to': 100, 'key': '50-100'},
# #             {'from': 100, 'to': 500, 'key': '100-500'},
# #             {'from': 500, 'key': '500+'}
# #         ])
        
# #         try:
# #             response = search.execute()
            
# #             # Process results
# #             products = []
# #             for hit in response:
# #                 products.append({
# #                     'product_id': hit.product_id,
# #                     'name': hit.name,
# #                     'description': hit.description,
# #                     'price': hit.price,
# #                     'category_name': hit.category_name,
# #                     'subcategory_name': hit.subcategory_name,
# #                     'brand': hit.brand,
# #                     'stock_quantity': hit.stock_quantity,
# #                     'primary_image_url': hit.primary_image_url,
# #                     'sku': hit.sku,
# #                     'score': hit.meta.score
# #                 })
            
# #             # Process aggregations
# #             facets = {}
# #             if hasattr(response.aggregations, 'categories'):
# #                 facets['categories'] = [
# #                     {'name': bucket.key, 'count': bucket.doc_count}
# #                     for bucket in response.aggregations.categories.buckets
# #                 ]
            
# #             if hasattr(response.aggregations, 'brands'):
# #                 facets['brands'] = [
# #                     {'name': bucket.key, 'count': bucket.doc_count}
# #                     for bucket in response.aggregations.brands.buckets
# #                 ]
            
# #             if hasattr(response.aggregations, 'price_ranges'):
# #                 facets['price_ranges'] = [
# #                     {'range': bucket.key, 'count': bucket.doc_count}
# #                     for bucket in response.aggregations.price_ranges.buckets
# #                 ]
            
# #             return {
# #                 'products': products,
# #                 'total': response.hits.total.value,
# #                 'page': page,
# #                 'size': size,
# #                 'total_pages': (response.hits.total.value + size - 1) // size,
# #                 'facets': facets,
# #                 'took': response.took
# #             }
            
# #         except Exception as e:
# #             logger.error(f"Search failed: {str(e)}")
# #             return {
# #                 'products': [],
# #                 'total': 0,
# #                 'page': page,
# #                 'size': size,
# #                 'total_pages': 0,
# #                 'facets': {},
# #                 'error': str(e)
# #             }
    
# #     @staticmethod
# #     def get_search_suggestions(query: str, size: int = 10) -> List[str]:
# #         """Get search suggestions/autocomplete"""
# #         if not query or len(query) < 2:
# #             return []
        
# #         search = Search(using=es_client, index='ecommerce_products')
        
# #         # Use completion suggester
# #         search = search.suggest('product_suggest', query, completion={
# #             'field': 'name.suggest',
# #             'size': size
# #         })
        
# #         # Also get prefix matches
# #         prefix_search = Search(using=es_client, index='ecommerce_products')
# #         prefix_search = prefix_search.query(
# #             Q('multi_match',
# #               query=query,
# #               fields=['name.autocomplete^2', 'category_name.text', 'brand.text'],
# #               type='bool_prefix')
# #         )[:size]
        
# #         try:
# #             suggestions = set()
            
# #             # Get completion suggestions
# #             response = search.execute()
# #             if hasattr(response, 'suggest') and 'product_suggest' in response.suggest:
# #                 for option in response.suggest.product_suggest[0].options:
# #                     suggestions.add(option._source.name)
            
# #             # Get prefix matches
# #             prefix_response = prefix_search.execute()
# #             for hit in prefix_response:
# #                 suggestions.add(hit.name)
# #                 if hit.category_name:
# #                     suggestions.add(hit.category_name)
# #                 if hit.brand:
# #                     suggestions.add(hit.brand)
            
# #             return list(suggestions)[:size]
            
# #         except Exception as e:
# #             logger.error(f"Suggestion search failed: {str(e)}")
# #             return []
    
# #     @staticmethod
# #     def delete_product(product_id: int) -> bool:
# #         """Delete a product from the index"""
# #         try:
# #             doc = ProductDocument.get(id=product_id)
# #             doc.delete()
# #             logger.info(f"Product {product_id} deleted from index")
# #             return True
# #         except Exception as e:
# #             logger.error(f"Failed to delete product {product_id}: {str(e)}")
# #             return False
    
# #     @staticmethod
# #     def reindex_all_products(db_session) -> Dict[str, int]:
# #         """Reindex all products from database"""
# #         try:
# #             # Delete existing index
# #             if es_client.indices.exists(index='ecommerce_products'):
# #                 es_client.indices.delete(index='ecommerce_products')
            
# #             # Recreate index
# #             ElasticsearchService.initialize_index()
            
# #             # Get all products from database
# #             from src.models.product import Product
# #             products = db_session.query(Product).filter(Product.is_active == True).all()
            
# #             # Bulk index
# #             result = ElasticsearchService.bulk_index_products(products)
            
# #             logger.info(f"Reindexing completed: {result}")
# #             return result
            
# #         except Exception as e:
# #             logger.error(f"Reindexing failed: {str(e)}")
# #             return {'success': 0, 'errors': 0, 'total': 0, 'error': str(e)}













# # src/services/search.py - Fixed version with is_available method
# from typing import List, Dict, Any, Optional
# import logging

# logger = logging.getLogger(__name__)

# # Try to import Elasticsearch components, but handle gracefully if not available
# try:
#     from elasticsearch_dsl import Search, Q
#     from elasticsearch.helpers import bulk
#     from src.documents.search import ProductDocument
#     from config.elasticsearch import es_client
#     ELASTICSEARCH_AVAILABLE = es_client is not None
# except ImportError as e:
#     logger.warning(f"Elasticsearch not available: {str(e)}")
#     ELASTICSEARCH_AVAILABLE = False
#     es_client = None
#     ProductDocument = None
#     Search = None
#     Q = None
#     bulk = None
# except Exception as e:
#     logger.error(f"Elasticsearch configuration error: {str(e)}")
#     ELASTICSEARCH_AVAILABLE = False
#     es_client = None
#     ProductDocument = None
#     Search = None
#     Q = None
#     bulk = None

# from src.models.product import Product

# class ElasticsearchService:
    
#     @staticmethod
#     def is_available() -> bool:
#         """Check if Elasticsearch is available"""
#         return ELASTICSEARCH_AVAILABLE and es_client is not None
    
#     @staticmethod
#     def initialize_index():
#         """Initialize the Elasticsearch index"""
#         if not ElasticsearchService.is_available():
#             logger.warning("Elasticsearch not available - skipping index initialization")
#             return False
            
#         try:
#             if ProductDocument:
#                 ProductDocument.init()
#                 logger.info("Elasticsearch index initialized successfully")
#                 return True
#             else:
#                 logger.warning("ProductDocument not available")
#                 return False
#         except Exception as e:
#             logger.error(f"Failed to initialize Elasticsearch index: {str(e)}")
#             return False
    
#     @staticmethod
#     def index_product(product: Product) -> bool:
#         """Index a single product"""
#         if not ElasticsearchService.is_available():
#             logger.debug(f"Elasticsearch not available - skipping indexing for product {product.product_id}")
#             return False
            
#         if not ProductDocument:
#             logger.warning("ProductDocument not available for indexing")
#             return False
            
#         try:
#             # Get effective price
#             effective_price = None
#             if product.calculated_price is not None:
#                 effective_price = product.calculated_price / 100
#             elif product.base_price is not None:
#                 effective_price = product.base_price / 100
#             elif product.price is not None:
#                 effective_price = float(product.price)
            
#             # Create search keywords from various fields
#             search_keywords = []
#             if product.name:
#                 search_keywords.append(product.name)
#             if product.description:
#                 search_keywords.append(product.description)
#             if hasattr(product, 'category') and product.category and hasattr(product.category, 'name'):
#                 search_keywords.append(product.category.name)
#             if hasattr(product, 'subcategory') and product.subcategory and hasattr(product.subcategory, 'name'):
#                 search_keywords.append(product.subcategory.name)
            
#             # Extract brand from specifications or name
#             brand = None
#             if product.specifications and isinstance(product.specifications, dict):
#                 brand = product.specifications.get('Brand') or product.specifications.get('brand')
            
#             # Create document
#             doc = ProductDocument(
#                 meta={'id': product.product_id},
#                 product_id=product.product_id,
#                 name=product.name,
#                 description=product.description,
#                 price=effective_price,
#                 base_price=product.base_price,
#                 calculated_price=product.calculated_price,
#                 category_id=product.category_id,
#                 category_name=product.category.name if hasattr(product, 'category') and product.category else None,
#                 subcategory_id=product.subcategory_id,
#                 subcategory_name=product.subcategory.name if hasattr(product, 'subcategory') and product.subcategory else None,
#                 brand=brand,
#                 sku=product.sku,
#                 stock_quantity=product.stock_quantity,
#                 storage_capacity=product.storage_capacity,
#                 specifications=str(product.specifications) if product.specifications else "",
#                 primary_image_url=product.primary_image_url,
#                 search_keywords=' '.join(search_keywords),
#                 popularity_score=1.0,
#                 is_active=product.is_active,
#                 created_at=product.created_at,
#                 updated_at=product.updated_at
#             )
            
#             doc.save()
#             logger.info(f"Product {product.product_id} indexed successfully")
#             return True
            
#         except Exception as e:
#             logger.error(f"Failed to index product {product.product_id}: {str(e)}")
#             return False
    
#     @staticmethod
#     def bulk_index_products(products: List[Product]) -> Dict[str, int]:
#         """Bulk index multiple products"""
#         if not ElasticsearchService.is_available():
#             logger.warning("Elasticsearch not available - skipping bulk indexing")
#             return {
#                 'success': 0,
#                 'errors': len(products),
#                 'total': len(products),
#                 'message': 'Elasticsearch not available'
#             }
        
#         if not bulk:
#             logger.warning("Bulk function not available")
#             return {
#                 'success': 0,
#                 'errors': len(products),
#                 'total': len(products),
#                 'message': 'Bulk function not available'
#             }
            
#         success_count = 0
#         error_count = 0
        
#         def generate_docs():
#             for product in products:
#                 try:
#                     # Get effective price
#                     effective_price = None
#                     if product.calculated_price is not None:
#                         effective_price = product.calculated_price / 100
#                     elif product.base_price is not None:
#                         effective_price = product.base_price / 100
#                     elif product.price is not None:
#                         effective_price = float(product.price)
                    
#                     # Create search keywords
#                     search_keywords = []
#                     if product.name:
#                         search_keywords.append(product.name)
#                     if product.description:
#                         search_keywords.append(product.description)
#                     if hasattr(product, 'category') and product.category and hasattr(product.category, 'name'):
#                         search_keywords.append(product.category.name)
                    
#                     # Extract brand
#                     brand = None
#                     if product.specifications and isinstance(product.specifications, dict):
#                         brand = product.specifications.get('Brand') or product.specifications.get('brand')
                    
#                     yield {
#                         '_index': 'ecommerce_products',
#                         '_id': product.product_id,
#                         '_source': {
#                             'product_id': product.product_id,
#                             'name': product.name,
#                             'description': product.description,
#                             'price': effective_price,
#                             'base_price': product.base_price,
#                             'calculated_price': product.calculated_price,
#                             'category_id': product.category_id,
#                             'category_name': product.category.name if hasattr(product, 'category') and product.category else None,
#                             'subcategory_id': product.subcategory_id,
#                             'subcategory_name': product.subcategory.name if hasattr(product, 'subcategory') and product.subcategory else None,
#                             'brand': brand,
#                             'sku': product.sku,
#                             'stock_quantity': product.stock_quantity,
#                             'storage_capacity': product.storage_capacity,
#                             'specifications': str(product.specifications) if product.specifications else "",
#                             'primary_image_url': product.primary_image_url,
#                             'search_keywords': ' '.join(search_keywords),
#                             'popularity_score': 1.0,
#                             'is_active': product.is_active,
#                             'created_at': product.created_at,
#                             'updated_at': product.updated_at
#                         }
#                     }
#                 except Exception as e:
#                     logger.error(f"Error preparing product {product.product_id} for indexing: {str(e)}")
#                     continue
        
#         try:
#             success, failed = bulk(es_client, generate_docs())
#             success_count = success
#             error_count = len(failed)
            
#             logger.info(f"Bulk indexing completed: {success_count} success, {error_count} errors")
            
#         except Exception as e:
#             logger.error(f"Bulk indexing failed: {str(e)}")
#             error_count = len(products)
        
#         return {
#             'success': success_count,
#             'errors': error_count,
#             'total': len(products)
#         }
    
#     @staticmethod
#     def search_products(
#         query: str,
#         category_id: Optional[int] = None,
#         subcategory_id: Optional[int] = None,
#         min_price: Optional[float] = None,
#         max_price: Optional[float] = None,
#         brand: Optional[str] = None,
#         in_stock_only: bool = True,
#         sort_by: str = 'relevance',
#         page: int = 1,
#         size: int = 20
#     ) -> Dict[str, Any]:
#         """Advanced product search with filters"""
        
#         if not ElasticsearchService.is_available():
#             logger.warning("Elasticsearch not available - returning empty search results")
#             return {
#                 'products': [],
#                 'total': 0,
#                 'page': page,
#                 'size': size,
#                 'total_pages': 0,
#                 'facets': {},
#                 'took': 0,
#                 'error': 'Elasticsearch search not available. Please start Elasticsearch server.'
#             }
        
#         if not Search or not Q:
#             logger.warning("Search components not available")
#             return {
#                 'products': [],
#                 'total': 0,
#                 'page': page,
#                 'size': size,
#                 'total_pages': 0,
#                 'facets': {},
#                 'took': 0,
#                 'error': 'Search components not available'
#             }
        
#         try:
#             search = Search(using=es_client, index='ecommerce_products')
            
#             # Base query - multi-field search
#             if query:
#                 search_query = Q('multi_match', 
#                                query=query,
#                                fields=[
#                                    'name^3',  # Boost name matches
#                                    'name.autocomplete^2',
#                                    'description',
#                                    'category_name.text',
#                                    'subcategory_name.text',
#                                    'brand.text',
#                                    'search_keywords',
#                                    'specifications'
#                                ],
#                                fuzziness='AUTO',
#                                operator='and')
#             else:
#                 search_query = Q('match_all')
            
#             # Apply filters
#             filters = []
            
#             # Active products only
#             filters.append(Q('term', is_active=True))
            
#             # Stock filter
#             if in_stock_only:
#                 filters.append(Q('range', stock_quantity={'gt': 0}))
            
#             # Category filter
#             if category_id:
#                 filters.append(Q('term', category_id=category_id))
            
#             # Subcategory filter
#             if subcategory_id:
#                 filters.append(Q('term', subcategory_id=subcategory_id))
            
#             # Price range filter
#             if min_price is not None or max_price is not None:
#                 price_range = {}
#                 if min_price is not None:
#                     price_range['gte'] = min_price
#                 if max_price is not None:
#                     price_range['lte'] = max_price
#                 filters.append(Q('range', price=price_range))
            
#             # Brand filter
#             if brand:
#                 filters.append(Q('term', brand=brand))
            
#             # Combine query and filters
#             if filters:
#                 search = search.query(Q('bool', must=[search_query], filter=filters))
#             else:
#                 search = search.query(search_query)
            
#             # Sorting
#             if sort_by == 'price_low':
#                 search = search.sort('price')
#             elif sort_by == 'price_high':
#                 search = search.sort('-price')
#             elif sort_by == 'newest':
#                 search = search.sort('-created_at')
#             elif sort_by == 'popularity':
#                 search = search.sort('-popularity_score', '_score')
#             else:  # relevance (default)
#                 search = search.sort('_score')
            
#             # Pagination
#             start = (page - 1) * size
#             search = search[start:start + size]
            
#             # Add aggregations for facets
#             search.aggs.bucket('categories', 'terms', field='category_name', size=10)
#             search.aggs.bucket('brands', 'terms', field='brand', size=10)
#             search.aggs.bucket('price_ranges', 'range', field='price', ranges=[
#                 {'from': 0, 'to': 50, 'key': '0-50'},
#                 {'from': 50, 'to': 100, 'key': '50-100'},
#                 {'from': 100, 'to': 500, 'key': '100-500'},
#                 {'from': 500, 'key': '500+'}
#             ])
            
#             response = search.execute()
            
#             # Process results
#             products = []
#             for hit in response:
#                 products.append({
#                     'product_id': hit.product_id,
#                     'name': hit.name,
#                     'description': hit.description,
#                     'price': hit.price,
#                     'category_name': hit.category_name,
#                     'subcategory_name': hit.subcategory_name,
#                     'brand': hit.brand,
#                     'stock_quantity': hit.stock_quantity,
#                     'primary_image_url': hit.primary_image_url,
#                     'sku': hit.sku,
#                     'score': hit.meta.score
#                 })
            
#             # Process aggregations
#             facets = {}
#             if hasattr(response.aggregations, 'categories'):
#                 facets['categories'] = [
#                     {'name': bucket.key, 'count': bucket.doc_count}
#                     for bucket in response.aggregations.categories.buckets
#                 ]
            
#             if hasattr(response.aggregations, 'brands'):
#                 facets['brands'] = [
#                     {'name': bucket.key, 'count': bucket.doc_count}
#                     for bucket in response.aggregations.brands.buckets
#                 ]
            
#             if hasattr(response.aggregations, 'price_ranges'):
#                 facets['price_ranges'] = [
#                     {'range': bucket.key, 'count': bucket.doc_count}
#                     for bucket in response.aggregations.price_ranges.buckets
#                 ]
            
#             return {
#                 'products': products,
#                 'total': response.hits.total.value,
#                 'page': page,
#                 'size': size,
#                 'total_pages': (response.hits.total.value + size - 1) // size,
#                 'facets': facets,
#                 'took': response.took
#             }
            
#         except Exception as e:
#             logger.error(f"Search failed: {str(e)}")
#             return {
#                 'products': [],
#                 'total': 0,
#                 'page': page,
#                 'size': size,
#                 'total_pages': 0,
#                 'facets': {},
#                 'took': 0,
#                 'error': str(e)
#             }
    
#     @staticmethod
#     def get_search_suggestions(query: str, size: int = 10) -> List[str]:
#         """Get search suggestions/autocomplete"""
#         if not ElasticsearchService.is_available():
#             logger.debug("Elasticsearch not available - returning empty suggestions")
#             return []
        
#         if not Search or not Q:
#             logger.warning("Search components not available for suggestions")
#             return []
            
#         if not query or len(query) < 2:
#             return []
        
#         try:
#             # Get prefix matches
#             prefix_search = Search(using=es_client, index='ecommerce_products')
#             prefix_search = prefix_search.query(
#                 Q('multi_match',
#                   query=query,
#                   fields=['name.autocomplete^2', 'category_name.text', 'brand.text'],
#                   type='bool_prefix')
#             )[:size]
            
#             suggestions = set()
            
#             # Get prefix matches
#             prefix_response = prefix_search.execute()
#             for hit in prefix_response:
#                 if hasattr(hit, 'name') and hit.name:
#                     suggestions.add(hit.name)
#                 if hasattr(hit, 'category_name') and hit.category_name:
#                     suggestions.add(hit.category_name)
#                 if hasattr(hit, 'brand') and hit.brand:
#                     suggestions.add(hit.brand)
            
#             return list(suggestions)[:size]
            
#         except Exception as e:
#             logger.error(f"Suggestion search failed: {str(e)}")
#             return []
    
#     @staticmethod
#     def delete_product(product_id: int) -> bool:
#         """Delete a product from the index"""
#         if not ElasticsearchService.is_available():
#             logger.debug(f"Elasticsearch not available - skipping deletion for product {product_id}")
#             return False
        
#         if not ProductDocument:
#             logger.warning("ProductDocument not available for deletion")
#             return False
            
#         try:
#             doc = ProductDocument.get(id=product_id)
#             doc.delete()
#             logger.info(f"Product {product_id} deleted from index")
#             return True
#         except Exception as e:
#             logger.error(f"Failed to delete product {product_id}: {str(e)}")
#             return False
    
#     @staticmethod
#     def reindex_all_products(db_session) -> Dict[str, int]:
#         """Reindex all products from database"""
#         if not ElasticsearchService.is_available():
#             logger.warning("Elasticsearch not available - cannot reindex products")
#             return {
#                 'success': 0, 
#                 'errors': 0, 
#                 'total': 0, 
#                 'message': 'Elasticsearch not available. Please start Elasticsearch server.'
#             }
            
#         try:
#             # Delete existing index
#             if es_client.indices.exists(index='ecommerce_products'):
#                 es_client.indices.delete(index='ecommerce_products')
            
#             # Recreate index
#             ElasticsearchService.initialize_index()
            
#             # Get all products from database
#             products = db_session.query(Product).filter(Product.is_active == True).all()
            
#             # Bulk index
#             result = ElasticsearchService.bulk_index_products(products)
            
#             logger.info(f"Reindexing completed: {result}")
#             return result
            
#         except Exception as e:
#             logger.error(f"Reindexing failed: {str(e)}")
#             return {'success': 0, 'errors': 0, 'total': 0, 'error': str(e)}














# src/services/search.py - Fixed version with better error handling
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Initialize variables
ELASTICSEARCH_AVAILABLE = False
es_client = None
ProductDocument = None
Search = None
Q = None
bulk = None

# Try to import Elasticsearch components
try:
    print("🔄 Attempting to import Elasticsearch components...")
    
    # Import Elasticsearch client first
    try:
        from config.elasticsearch import es_client as imported_es_client
        es_client = imported_es_client
        print("✅ Elasticsearch client imported successfully")
    except Exception as e:
        print(f"❌ Failed to import Elasticsearch client: {str(e)}")
        raise e
    
    # Import Elasticsearch DSL components
    try:
        from elasticsearch_dsl import Search, Q
        print("✅ Search and Q imported successfully")
    except Exception as e:
        print(f"❌ Failed to import Search/Q: {str(e)}")
        raise e
    
    # Import bulk helper
    try:
        from elasticsearch.helpers import bulk
        print("✅ Bulk helper imported successfully")
    except Exception as e:
        print(f"❌ Failed to import bulk helper: {str(e)}")
        raise e
    
    # Import ProductDocument
    try:
        from src.documents.search import ProductDocument
        print("✅ ProductDocument imported successfully")
    except Exception as e:
        print(f"❌ Failed to import ProductDocument: {str(e)}")
        raise e
    
    # Test if client is working
    if es_client and es_client.ping():
        ELASTICSEARCH_AVAILABLE = True
        print("✅ Elasticsearch is available and responding")
    else:
        print("❌ Elasticsearch client exists but not responding")
        ELASTICSEARCH_AVAILABLE = False
        
except ImportError as e:
    logger.warning(f"Elasticsearch import error: {str(e)}")
    print(f"❌ Import error: {str(e)}")
    ELASTICSEARCH_AVAILABLE = False
except Exception as e:
    logger.error(f"Elasticsearch configuration error: {str(e)}")
    print(f"❌ Configuration error: {str(e)}")
    ELASTICSEARCH_AVAILABLE = False

from src.models.product import Product

class ElasticsearchService:
    
    @staticmethod
    def is_available() -> bool:
        """Check if Elasticsearch is available"""
        global ELASTICSEARCH_AVAILABLE, es_client
        
        # Re-check availability if not already available
        if not ELASTICSEARCH_AVAILABLE and es_client:
            try:
                if es_client.ping():
                    ELASTICSEARCH_AVAILABLE = True
                    print("✅ Elasticsearch reconnected successfully")
            except:
                pass
        
        return ELASTICSEARCH_AVAILABLE and es_client is not None
    
    @staticmethod
    def initialize_index():
        """Initialize the Elasticsearch index"""
        if not ElasticsearchService.is_available():
            logger.warning("Elasticsearch not available - skipping index initialization")
            return False
            
        try:
            if ProductDocument:
                ProductDocument.init()
                logger.info("Elasticsearch index initialized successfully")
                print("✅ Elasticsearch index initialized")
                return True
            else:
                logger.warning("ProductDocument not available")
                print("❌ ProductDocument not available")
                return False
        except Exception as e:
            logger.error(f"Failed to initialize Elasticsearch index: {str(e)}")
            print(f"❌ Failed to initialize index: {str(e)}")
            return False
    
    @staticmethod
    def index_product(product: Product) -> bool:
        """Index a single product"""
        if not ElasticsearchService.is_available():
            logger.debug(f"Elasticsearch not available - skipping indexing for product {product.product_id}")
            return False
            
        if not ProductDocument:
            logger.warning("ProductDocument not available for indexing")
            return False
            
        try:
            print(f"🔄 Indexing product: {product.name}")
            
            # Get effective price
            effective_price = None
            if product.calculated_price is not None:
                effective_price = product.calculated_price / 100
            elif product.base_price is not None:
                effective_price = product.base_price / 100
            elif product.price is not None:
                effective_price = float(product.price)
            
            # Create search keywords from various fields
            search_keywords = []
            if product.name:
                search_keywords.append(product.name)
            if product.description:
                search_keywords.append(product.description)
            if hasattr(product, 'category') and product.category and hasattr(product.category, 'name'):
                search_keywords.append(product.category.name)
            if hasattr(product, 'subcategory') and product.subcategory and hasattr(product.subcategory, 'name'):
                search_keywords.append(product.subcategory.name)
            
            # Extract brand from specifications or name
            brand = None
            if product.specifications and isinstance(product.specifications, dict):
                brand = product.specifications.get('Brand') or product.specifications.get('brand')
            
            # Create document
            doc = ProductDocument(
                meta={'id': product.product_id},
                product_id=product.product_id,
                name=product.name,
                description=product.description,
                price=effective_price,
                base_price=product.base_price,
                calculated_price=product.calculated_price,
                category_id=product.category_id,
                category_name=product.category.name if hasattr(product, 'category') and product.category else None,
                subcategory_id=product.subcategory_id,
                subcategory_name=product.subcategory.name if hasattr(product, 'subcategory') and product.subcategory else None,
                brand=brand,
                sku=product.sku,
                stock_quantity=product.stock_quantity,
                storage_capacity=product.storage_capacity,
                specifications=str(product.specifications) if product.specifications else "",
                primary_image_url=product.primary_image_url,
                search_keywords=' '.join(search_keywords),
                popularity_score=1.0,
                is_active=product.is_active,
                created_at=product.created_at,
                updated_at=product.updated_at
            )
            
            doc.save()
            logger.info(f"Product {product.product_id} indexed successfully")
            print(f"✅ Product {product.product_id} indexed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index product {product.product_id}: {str(e)}")
            print(f"❌ Failed to index product {product.product_id}: {str(e)}")
            return False
    
    @staticmethod
    def bulk_index_products(products: List[Product]) -> Dict[str, int]:
        """Bulk index multiple products"""
        if not ElasticsearchService.is_available():
            logger.warning("Elasticsearch not available - skipping bulk indexing")
            return {
                'success': 0,
                'errors': len(products),
                'total': len(products),
                'message': 'Elasticsearch not available'
            }
        
        if not bulk:
            logger.warning("Bulk function not available")
            return {
                'success': 0,
                'errors': len(products),
                'total': len(products),
                'message': 'Bulk function not available'
            }
            
        success_count = 0
        error_count = 0
        
        print(f"🔄 Bulk indexing {len(products)} products...")
        
        def generate_docs():
            for product in products:
                try:
                    # Get effective price
                    effective_price = None
                    if product.calculated_price is not None:
                        effective_price = product.calculated_price / 100
                    elif product.base_price is not None:
                        effective_price = product.base_price / 100
                    elif product.price is not None:
                        effective_price = float(product.price)
                    
                    # Create search keywords
                    search_keywords = []
                    if product.name:
                        search_keywords.append(product.name)
                    if product.description:
                        search_keywords.append(product.description)
                    if hasattr(product, 'category') and product.category and hasattr(product.category, 'name'):
                        search_keywords.append(product.category.name)
                    
                    # Extract brand
                    brand = None
                    if product.specifications and isinstance(product.specifications, dict):
                        brand = product.specifications.get('Brand') or product.specifications.get('brand')
                    
                    yield {
                        '_index': 'ecommerce_products',
                        '_id': product.product_id,
                        '_source': {
                            'product_id': product.product_id,
                            'name': product.name,
                            'description': product.description,
                            'price': effective_price,
                            'base_price': product.base_price,
                            'calculated_price': product.calculated_price,
                            'category_id': product.category_id,
                            'category_name': product.category.name if hasattr(product, 'category') and product.category else None,
                            'subcategory_id': product.subcategory_id,
                            'subcategory_name': product.subcategory.name if hasattr(product, 'subcategory') and product.subcategory else None,
                            'brand': brand,
                            'sku': product.sku,
                            'stock_quantity': product.stock_quantity,
                            'storage_capacity': product.storage_capacity,
                            'specifications': str(product.specifications) if product.specifications else "",
                            'primary_image_url': product.primary_image_url,
                            'search_keywords': ' '.join(search_keywords),
                            'popularity_score': 1.0,
                            'is_active': product.is_active,
                            'created_at': product.created_at,
                            'updated_at': product.updated_at
                        }
                    }
                except Exception as e:
                    logger.error(f"Error preparing product {product.product_id} for indexing: {str(e)}")
                    continue
        
        try:
            success, failed = bulk(es_client, generate_docs())
            success_count = success
            error_count = len(failed)
            
            logger.info(f"Bulk indexing completed: {success_count} success, {error_count} errors")
            print(f"✅ Bulk indexing completed: {success_count} success, {error_count} errors")
            
        except Exception as e:
            logger.error(f"Bulk indexing failed: {str(e)}")
            print(f"❌ Bulk indexing failed: {str(e)}")
            error_count = len(products)
        
        return {
            'success': success_count,
            'errors': error_count,
            'total': len(products)
        }
    
    @staticmethod
    def search_products(
        query: str,
        category_id: Optional[int] = None,
        subcategory_id: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        brand: Optional[str] = None,
        in_stock_only: bool = True,
        sort_by: str = 'relevance',
        page: int = 1,
        size: int = 20
    ) -> Dict[str, Any]:
        """Advanced product search with filters"""
        
        if not ElasticsearchService.is_available():
            logger.warning("Elasticsearch not available - returning empty search results")
            print("❌ Elasticsearch not available for search")
            return {
                'products': [],
                'total': 0,
                'page': page,
                'size': size,
                'total_pages': 0,
                'facets': {},
                'took': 0,
                'error': 'Elasticsearch search not available. Please start Elasticsearch server.'
            }
        
        if not Search or not Q:
            logger.warning("Search components not available")
            print("❌ Search components not available")
            return {
                'products': [],
                'total': 0,
                'page': page,
                'size': size,
                'total_pages': 0,
                'facets': {},
                'took': 0,
                'error': 'Search components not available'
            }
        
        try:
            print(f"🔍 Searching for: '{query}'")
            search = Search(using=es_client, index='ecommerce_products')
            
            # Base query - multi-field search
            if query:
                search_query = Q('multi_match', 
                               query=query,
                               fields=[
                                   'name^3',  # Boost name matches
                                   'name.autocomplete^2',
                                   'description',
                                   'category_name.text',
                                   'subcategory_name.text',
                                   'brand.text',
                                   'search_keywords',
                                   'specifications'
                               ],
                               fuzziness='AUTO',
                               operator='and')
            else:
                search_query = Q('match_all')
            
            # Apply filters
            filters = []
            
            # Active products only
            filters.append(Q('term', is_active=True))
            
            # Stock filter
            if in_stock_only:
                filters.append(Q('range', stock_quantity={'gt': 0}))
            
            # Category filter
            if category_id:
                filters.append(Q('term', category_id=category_id))
            
            # Subcategory filter
            if subcategory_id:
                filters.append(Q('term', subcategory_id=subcategory_id))
            
            # Price range filter
            if min_price is not None or max_price is not None:
                price_range = {}
                if min_price is not None:
                    price_range['gte'] = min_price
                if max_price is not None:
                    price_range['lte'] = max_price
                filters.append(Q('range', price=price_range))
            
            # Brand filter
            if brand:
                filters.append(Q('term', brand=brand))
            
            # Combine query and filters
            if filters:
                search = search.query(Q('bool', must=[search_query], filter=filters))
            else:
                search = search.query(search_query)
            
            # Sorting
            if sort_by == 'price_low':
                search = search.sort('price')
            elif sort_by == 'price_high':
                search = search.sort('-price')
            elif sort_by == 'newest':
                search = search.sort('-created_at')
            elif sort_by == 'popularity':
                search = search.sort('-popularity_score', '_score')
            else:  # relevance (default)
                search = search.sort('_score')
            
            # Pagination
            start = (page - 1) * size
            search = search[start:start + size]
            
            # Add aggregations for facets
            search.aggs.bucket('categories', 'terms', field='category_name', size=10)
            search.aggs.bucket('brands', 'terms', field='brand', size=10)
            search.aggs.bucket('price_ranges', 'range', field='price', ranges=[
                {'from': 0, 'to': 50, 'key': '0-50'},
                {'from': 50, 'to': 100, 'key': '50-100'},
                {'from': 100, 'to': 500, 'key': '100-500'},
                {'from': 500, 'key': '500+'}
            ])
            
            response = search.execute()
            
            # Process results
            products = []
            for hit in response:
                products.append({
                    'product_id': hit.product_id,
                    'name': hit.name,
                    'description': hit.description,
                    'price': hit.price,
                    'category_name': hit.category_name,
                    'subcategory_name': hit.subcategory_name,
                    'brand': hit.brand,
                    'stock_quantity': hit.stock_quantity,
                    'primary_image_url': hit.primary_image_url,
                    'sku': hit.sku,
                    'score': hit.meta.score
                })
            
            # Process aggregations
            facets = {}
            if hasattr(response.aggregations, 'categories'):
                facets['categories'] = [
                    {'name': bucket.key, 'count': bucket.doc_count}
                    for bucket in response.aggregations.categories.buckets
                ]
            
            if hasattr(response.aggregations, 'brands'):
                facets['brands'] = [
                    {'name': bucket.key, 'count': bucket.doc_count}
                    for bucket in response.aggregations.brands.buckets
                ]
            
            if hasattr(response.aggregations, 'price_ranges'):
                facets['price_ranges'] = [
                    {'range': bucket.key, 'count': bucket.doc_count}
                    for bucket in response.aggregations.price_ranges.buckets
                ]
            
            print(f"✅ Search completed: {len(products)} products found")
            
            return {
                'products': products,
                'total': response.hits.total.value,
                'page': page,
                'size': size,
                'total_pages': (response.hits.total.value + size - 1) // size,
                'facets': facets,
                'took': response.took
            }
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            print(f"❌ Search failed: {str(e)}")
            return {
                'products': [],
                'total': 0,
                'page': page,
                'size': size,
                'total_pages': 0,
                'facets': {},
                'took': 0,
                'error': str(e)
            }
    
    @staticmethod
    def get_search_suggestions(query: str, size: int = 10) -> List[str]:
        """Get search suggestions/autocomplete"""
        if not ElasticsearchService.is_available():
            logger.debug("Elasticsearch not available - returning empty suggestions")
            return []
        
        if not Search or not Q:
            logger.warning("Search components not available for suggestions")
            return []
            
        if not query or len(query) < 2:
            return []
        
        try:
            # Get prefix matches
            prefix_search = Search(using=es_client, index='ecommerce_products')
            prefix_search = prefix_search.query(
                Q('multi_match',
                  query=query,
                  fields=['name.autocomplete^2', 'category_name.text', 'brand.text'],
                  type='bool_prefix')
            )[:size]
            
            suggestions = set()
            
            # Get prefix matches
            prefix_response = prefix_search.execute()
            for hit in prefix_response:
                if hasattr(hit, 'name') and hit.name:
                    suggestions.add(hit.name)
                if hasattr(hit, 'category_name') and hit.category_name:
                    suggestions.add(hit.category_name)
                if hasattr(hit, 'brand') and hit.brand:
                    suggestions.add(hit.brand)
            
            return list(suggestions)[:size]
            
        except Exception as e:
            logger.error(f"Suggestion search failed: {str(e)}")
            return []
    
    @staticmethod
    def delete_product(product_id: int) -> bool:
        """Delete a product from the index"""
        if not ElasticsearchService.is_available():
            logger.debug(f"Elasticsearch not available - skipping deletion for product {product_id}")
            return False
        
        if not ProductDocument:
            logger.warning("ProductDocument not available for deletion")
            return False
            
        try:
            doc = ProductDocument.get(id=product_id)
            doc.delete()
            logger.info(f"Product {product_id} deleted from index")
            return True
        except Exception as e:
            logger.error(f"Failed to delete product {product_id}: {str(e)}")
            return False
    
    @staticmethod
    def reindex_all_products(db_session) -> Dict[str, int]:
        """Reindex all products from database"""
        if not ElasticsearchService.is_available():
            logger.warning("Elasticsearch not available - cannot reindex products")
            return {
                'success': 0, 
                'errors': 0, 
                'total': 0, 
                'message': 'Elasticsearch not available. Please start Elasticsearch server.'
            }
            
        try:
            print("🔄 Starting reindex process...")
            
            # Delete existing index
            if es_client.indices.exists(index='ecommerce_products'):
                es_client.indices.delete(index='ecommerce_products')
                print("🗑️ Deleted existing index")
            
            # Recreate index
            ElasticsearchService.initialize_index()
            
            # Get all products from database
            products = db_session.query(Product).filter(Product.is_active == True).all()
            print(f"📊 Found {len(products)} active products to index")
            
            # Bulk index
            result = ElasticsearchService.bulk_index_products(products)
            
            logger.info(f"Reindexing completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Reindexing failed: {str(e)}")
            print(f"❌ Reindexing failed: {str(e)}")
            return {'success': 0, 'errors': 0, 'total': 0, 'error': str(e)}