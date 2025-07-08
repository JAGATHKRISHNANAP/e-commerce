# # # src/documents/search.py
# # from elasticsearch_dsl import Document, Text, Keyword, Integer, Float, Date, Completion, analyzer,Boolean
# # from datetime import datetime

# # # Custom analyzers for better search
# # product_analyzer = analyzer(
# #     'product_analyzer',
# #     tokenizer='standard',
# #     filters=['lowercase', 'stop', 'snowball']
# # )

# # autocomplete_analyzer = analyzer(
# #     'autocomplete_analyzer',
# #     tokenizer='edge_ngram',
# #     filters=['lowercase']
# # )

# # class ProductDocument(Document):
# #     """Elasticsearch document for products"""
    
# #     # Basic product info
# #     product_id = Integer()
# #     name = Text(
# #         analyzer=product_analyzer,
# #         fields={
# #             'raw': Keyword(),
# #             'suggest': Completion(),
# #             'autocomplete': Text(analyzer=autocomplete_analyzer)
# #         }
# #     )
# #     description = Text(analyzer=product_analyzer)
    
# #     # Pricing
# #     price = Float()
# #     base_price = Integer()
# #     calculated_price = Integer()
    
# #     # Categories
# #     category_id = Integer()
# #     category_name = Keyword(
# #         fields={'text': Text(analyzer=product_analyzer)}
# #     )
# #     subcategory_id = Integer()
# #     subcategory_name = Keyword(
# #         fields={'text': Text(analyzer=product_analyzer)}
# #     )
    
# #     # Product attributes
# #     brand = Keyword(fields={'text': Text(analyzer=product_analyzer)})
# #     sku = Keyword()
# #     stock_quantity = Integer()
# #     storage_capacity = Keyword()
    
# #     # Specifications (dynamic)
# #     specifications = Text()
    
# #     # Images
# #     primary_image_url = Keyword()
    
# #     # Search optimization
# #     tags = Keyword()
# #     search_keywords = Text(analyzer=product_analyzer)
    
# #     # Metrics for ranking
# #     popularity_score = Float()
# #     rating = Float()
# #     review_count = Integer()
    
# #     # Status
# #     is_active = Boolean()
# #     created_at = Date()
# #     updated_at = Date()
    
# #     class Index:
# #         name = 'ecommerce_products'
# #         settings = {
# #             'number_of_shards': 1,
# #             'number_of_replicas': 0,
# #             'analysis': {
# #                 'analyzer': {
# #                     'product_analyzer': {
# #                         'type': 'custom',
# #                         'tokenizer': 'standard',
# #                         'filter': ['lowercase', 'stop', 'snowball']
# #                     },
# #                     'autocomplete_analyzer': {
# #                         'type': 'custom',
# #                         'tokenizer': 'edge_ngram_tokenizer',
# #                         'filter': ['lowercase']
# #                     }
# #                 },
# #                 'tokenizer': {
# #                     'edge_ngram_tokenizer': {
# #                         'type': 'edge_ngram',
# #                         'min_gram': 2,
# #                         'max_gram': 10,
# #                         'token_chars': ['letter', 'digit']
# #                     }
# #                 }
# #             }
# #         }














# # src/documents/search.py
# from elasticsearch_dsl import Document, Text, Keyword, Integer, Float, Boolean, Date, analyzer

# # Custom analyzer for autocomplete
# autocomplete_analyzer = analyzer(
#     'autocomplete',
#     tokenizer='edge_ngram',
#     filters=['lowercase']
# )

# class ProductDocument(Document):
#     """Elasticsearch document for products"""
    
#     # Basic product information
#     product_id = Integer()
#     name = Text(
#         analyzer='standard',
#         fields={
#             'autocomplete': Text(analyzer=autocomplete_analyzer),
#             'raw': Keyword()
#         }
#     )
#     description = Text(analyzer='standard')
#     sku = Keyword()
    
#     # Pricing
#     price = Float()
#     base_price = Integer()
#     calculated_price = Integer()
    
#     # Categories and classification
#     category_id = Integer()
#     category_name = Text(
#         fields={
#             'text': Text(analyzer='standard'),
#             'raw': Keyword()
#         }
#     )
#     subcategory_id = Integer()
#     subcategory_name = Text(
#         fields={
#             'text': Text(analyzer='standard'),
#             'raw': Keyword()
#         }
#     )
#     brand = Text(
#         fields={
#             'text': Text(analyzer='standard'),
#             'raw': Keyword()
#         }
#     )
    
#     # Inventory and specifications
#     stock_quantity = Integer()
#     storage_capacity = Keyword()
#     specifications = Text()
    
#     # Media and additional info
#     primary_image_url = Keyword()
#     search_keywords = Text(analyzer='standard')
#     popularity_score = Float()
    
#     # Status and timestamps
#     is_active = Boolean()
#     created_at = Date()
#     updated_at = Date()
    
#     class Index:
#         name = 'ecommerce_products'
#         settings = {
#             'number_of_shards': 1,
#             'number_of_replicas': 0,
#             'analysis': {
#                 'analyzer': {
#                     'autocomplete': {
#                         'tokenizer': 'edge_ngram',
#                         'filter': ['lowercase']
#                     }
#                 },
#                 'tokenizer': {
#                     'edge_ngram': {
#                         'type': 'edge_ngram',
#                         'min_gram': 2,
#                         'max_gram': 20,
#                         'token_chars': ['letter', 'digit']
#                     }
#                 }
#             }
#         }









from elasticsearch_dsl import Document, Text, Keyword, Integer, Float, Boolean, Date, analyzer

print("🔄 Loading ProductDocument class...")

# Custom analyzer for autocomplete
autocomplete_analyzer = analyzer(
    'autocomplete',
    tokenizer='edge_ngram',
    filters=['lowercase']
)

class ProductDocument(Document):
    """Elasticsearch document for products"""
    
    # Basic product information
    product_id = Integer()
    name = Text(
        analyzer='standard',
        fields={
            'autocomplete': Text(analyzer=autocomplete_analyzer),
            'raw': Keyword()
        }
    )
    description = Text(analyzer='standard')
    sku = Keyword()
    
    # Pricing
    price = Float()
    base_price = Integer()
    calculated_price = Integer()
    
    # Categories and classification
    category_id = Integer()
    category_name = Text(
        fields={
            'text': Text(analyzer='standard'),
            'raw': Keyword()
        }
    )
    subcategory_id = Integer()
    subcategory_name = Text(
        fields={
            'text': Text(analyzer='standard'),
            'raw': Keyword()
        }
    )
    brand = Text(
        fields={
            'text': Text(analyzer='standard'),
            'raw': Keyword()
        }
    )
    
    # Inventory and specifications
    stock_quantity = Integer()
    storage_capacity = Keyword()
    specifications = Text()
    
    # Media and additional info
    primary_image_url = Keyword()
    search_keywords = Text(analyzer='standard')
    popularity_score = Float()
    
    # Status and timestamps
    is_active = Boolean()
    created_at = Date()
    updated_at = Date()
    
    class Index:
        name = 'ecommerce_products'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'analysis': {
                'analyzer': {
                    'autocomplete': {
                        'tokenizer': 'edge_ngram',
                        'filter': ['lowercase']
                    }
                },
                'tokenizer': {
                    'edge_ngram': {
                        'type': 'edge_ngram',
                        'min_gram': 2,
                        'max_gram': 20,
                        'token_chars': ['letter', 'digit']
                    }
                }
            }
        }

print("✅ ProductDocument class loaded successfully")