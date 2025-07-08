# # # # config/elasticsearch.py
# # # from elasticsearch import Elasticsearch
# # # from elasticsearch_dsl import connections
# # # import os
# # # from typing import Optional

# # # class ElasticsearchConfig:
# # #     def __init__(self):
# # #         self.host = os.getenv('ELASTICSEARCH_HOST', 'localhost')
# # #         self.port = os.getenv('ELASTICSEARCH_PORT', '9200')
# # #         self.username = os.getenv('ELASTICSEARCH_USERNAME', 'elastic')
# # #         self.password = os.getenv('ELASTICSEARCH_PASSWORD', 'changeme')
# # #         self.use_ssl = os.getenv('ELASTICSEARCH_USE_SSL', 'false').lower() == 'true'
        
# # #     def get_client(self) -> Elasticsearch:
# # #         """Get Elasticsearch client"""
# # #         config = {
# # #             'hosts': [f'{self.host}:{self.port}'],
# # #             'verify_certs': False,
# # #             'ssl_show_warn': False,
# # #         }
        
# # #         if self.username and self.password:
# # #             config['basic_auth'] = (self.username, self.password)
            
# # #         if self.use_ssl:
# # #             config['scheme'] = 'https'
            
# # #         return Elasticsearch(**config)

# # # # Initialize global ES client
# # # es_config = ElasticsearchConfig()
# # # es_client = es_config.get_client()

# # # # Set up elasticsearch-dsl connection
# # # connections.create_connection(
# # #     hosts=[f'{es_config.host}:{es_config.port}'],
# # #     timeout=20
# # # )

# # # # src/search/documents.py
# # # from elasticsearch_dsl import Document, Text, Keyword, Integer, Float, Date, Completion, analyzer
# # # from datetime import datetime

# # # # Custom analyzers for better search
# # # product_analyzer = analyzer(
# # #     'product_analyzer',
# # #     tokenizer='standard',
# # #     filters=['lowercase', 'stop', 'snowball']
# # # )

# # # autocomplete_analyzer = analyzer(
# # #     'autocomplete_analyzer',
# # #     tokenizer='edge_ngram',
# # #     filters=['lowercase']
# # # )

# # # class ProductDocument(Document):
# # #     """Elasticsearch document for products"""
    
# # #     # Basic product info
# # #     product_id = Integer()
# # #     name = Text(
# # #         analyzer=product_analyzer,
# # #         fields={
# # #             'raw': Keyword(),
# # #             'suggest': Completion(),
# # #             'autocomplete': Text(analyzer=autocomplete_analyzer)
# # #         }
# # #     )
# # #     description = Text(analyzer=product_analyzer)
    
# # #     # Pricing
# # #     price = Float()
# # #     base_price = Integer()
# # #     calculated_price = Integer()
    
# # #     # Categories
# # #     category_id = Integer()
# # #     category_name = Keyword(
# # #         fields={'text': Text(analyzer=product_analyzer)}
# # #     )
# # #     subcategory_id = Integer()
# # #     subcategory_name = Keyword(
# # #         fields={'text': Text(analyzer=product_analyzer)}
# # #     )
    
# # #     # Product attributes
# # #     brand = Keyword(fields={'text': Text(analyzer=product_analyzer)})
# # #     sku = Keyword()
# # #     stock_quantity = Integer()
# # #     storage_capacity = Keyword()
    
# # #     # Specifications (dynamic)
# # #     specifications = Text()
    
# # #     # Images
# # #     primary_image_url = Keyword()
    
# # #     # Search optimization
# # #     tags = Keyword()
# # #     search_keywords = Text(analyzer=product_analyzer)
    
# # #     # Metrics for ranking
# # #     popularity_score = Float()
# # #     rating = Float()
# # #     review_count = Integer()
    
# # #     # Status
# # #     is_active = Boolean()
# # #     created_at = Date()
# # #     updated_at = Date()
    
# # #     class Index:
# # #         name = 'ecommerce_products'
# # #         settings = {
# # #             'number_of_shards': 1,
# # #             'number_of_replicas': 0,
# # #             'analysis': {
# # #                 'analyzer': {
# # #                     'product_analyzer': {
# # #                         'type': 'custom',
# # #                         'tokenizer': 'standard',
# # #                         'filter': ['lowercase', 'stop', 'snowball']
# # #                     },
# # #                     'autocomplete_analyzer': {
# # #                         'type': 'custom',
# # #                         'tokenizer': 'edge_ngram_tokenizer',
# # #                         'filter': ['lowercase']
# # #                     }
# # #                 },
# # #                 'tokenizer': {
# # #                     'edge_ngram_tokenizer': {
# # #                         'type': 'edge_ngram',
# # #                         'min_gram': 2,
# # #                         'max_gram': 10,
# # #                         'token_chars': ['letter', 'digit']
# # #                     }
# # #                 }
# # #             }
# # #         }






# # # config/elasticsearch.py - Fixed version for your setup
# # from elasticsearch import Elasticsearch
# # from elasticsearch_dsl import connections
# # import os
# # from typing import Optional
# # import logging

# # logger = logging.getLogger(__name__)

# # class ElasticsearchConfig:
# #     def __init__(self):
# #         self.host = os.getenv('ELASTICSEARCH_HOST', 'localhost')
# #         self.port = os.getenv('ELASTICSEARCH_PORT', '9200')
# #         self.username = os.getenv('ELASTICSEARCH_USERNAME', None)  # Changed to None
# #         self.password = os.getenv('ELASTICSEARCH_PASSWORD', None)  # Changed to None
# #         self.use_ssl = os.getenv('ELASTICSEARCH_USE_SSL', 'false').lower() == 'true'
        
# #     def get_client(self) -> Optional[Elasticsearch]:
# #         """Get Elasticsearch client with proper error handling"""
# #         try:
# #             # Build the full URL with proper scheme
# #             scheme = 'https' if self.use_ssl else 'http'
# #             full_url = f"{scheme}://{self.host}:{self.port}"
            
# #             config = {
# #                 'hosts': [full_url],  # Use full URL with scheme
# #                 'verify_certs': False,
# #                 'ssl_show_warn': False,
# #                 'request_timeout': 30,
# #                 'retry_on_timeout': True,
# #                 'max_retries': 3,
# #             }
            
# #             # Only add auth if both username and password are provided
# #             if self.username and self.password:
# #                 config['basic_auth'] = (self.username, self.password)
# #                 logger.info("Using basic authentication for Elasticsearch")
# #             else:
# #                 logger.info("No authentication configured for Elasticsearch")
            
# #             # Create client
# #             client = Elasticsearch(**config)
            
# #             # Test the connection
# #             if client.ping():
# #                 logger.info(f"Successfully connected to Elasticsearch at {full_url}")
# #                 return client
# #             else:
# #                 logger.warning(f"Could not ping Elasticsearch at {full_url}")
# #                 return None
                
# #         except Exception as e:
# #             logger.error(f"Failed to create Elasticsearch client: {str(e)}")
# #             logger.info("Your application will continue to work without search functionality")
# #             return None

# # # Initialize global ES config
# # es_config = ElasticsearchConfig()
# # es_client = es_config.get_client()

# # # Set up elasticsearch-dsl connection only if client is available
# # if es_client:
# #     try:
# #         scheme = 'https' if es_config.use_ssl else 'http'
# #         full_url = f"{scheme}://{es_config.host}:{es_config.port}"
        
# #         connections.create_connection(
# #             hosts=[full_url],
# #             timeout=20,
# #             verify_certs=False,
# #             ssl_show_warn=False,
# #         )
# #         logger.info("Elasticsearch DSL connection configured successfully")
# #     except Exception as e:
# #         logger.error(f"Failed to configure Elasticsearch DSL connection: {str(e)}")
# #         es_client = None
# # else:
# #     logger.warning("Elasticsearch client not available - search features will be disabled")
# #     logger.info("To enable search features, please install and start Elasticsearch")







# # config/elasticsearch.py
# from elasticsearch import Elasticsearch
# from config.settings import settings
# import logging

# logger = logging.getLogger(__name__)

# # Initialize Elasticsearch client
# es_client = None

# try:
#     # Create Elasticsearch client
#     es_client = Elasticsearch(
#         [f"http://{settings.elasticsearch_host}:{settings.elasticsearch_port}"],
#         verify_certs=False,
#         ssl_show_warn=False,
#         request_timeout=30,
#         retry_on_timeout=True,
#         max_retries=3
#     )
    
#     # Test connection
#     if es_client.ping():
#         logger.info(f"✅ Successfully connected to Elasticsearch at {settings.elasticsearch_host}:{settings.elasticsearch_port}")
#     else:
#         logger.warning("⚠️ Could not ping Elasticsearch server")
#         es_client = None
        
# except Exception as e:
#     logger.warning(f"❌ Elasticsearch connection failed: {str(e)}")
#     logger.info("🔧 To enable search features:")
#     logger.info("   1. Run: docker-compose up -d")
#     logger.info("   2. Wait 30 seconds for Elasticsearch to start")
#     logger.info("   3. Test: curl http://localhost:9200")
#     es_client = None


from elasticsearch import Elasticsearch
import logging

logger = logging.getLogger(__name__)

# Initialize Elasticsearch client
es_client = None

try:
    print("🔄 Attempting to connect to Elasticsearch...")
    
    # Create Elasticsearch client
    es_client = Elasticsearch(
        ["http://localhost:9200"],
        verify_certs=False,
        ssl_show_warn=False,
        request_timeout=30,
        retry_on_timeout=True,
        max_retries=3,
        # Add these for better compatibility
        ca_certs=None,
        http_auth=None,
        use_ssl=False
    )
    
    # Test connection
    if es_client.ping():
        logger.info("✅ Successfully connected to Elasticsearch at localhost:9200")
        print("✅ Elasticsearch connection successful!")
    else:
        logger.warning("⚠️ Could not ping Elasticsearch server")
        print("⚠️ Elasticsearch ping failed - server may be starting up")
        
except Exception as e:
    logger.warning(f"❌ Elasticsearch connection failed: {str(e)}")
    print(f"❌ Elasticsearch error: {str(e)}")
    print("🔧 To enable search features:")
    print("   1. Run: docker-compose up -d elasticsearch")
    print("   2. Wait 30 seconds for Elasticsearch to start")
    print("   3. Test: curl http://localhost:9200")
    es_client = None