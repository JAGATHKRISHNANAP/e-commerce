# # jagath  ELAKKIYA.COM

# # Updated app.py - Add search router and initialize Elasticsearch
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# from config.database import engine
# from src.models import Base
# from src.api.v1 import categories, products, auth, vender_auth, cart, addresses, orders, specifications, pricing, search, vendor_orders
# from src.services.search import ElasticsearchService
# import uvicorn
# import os
# import logging

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Import all models to ensure they're registered with SQLAlchemy
# from src.models.customer import Customer
# from src.models.otp import OTP
# from src.models.address import CustomerAddress
# from src.models.order import Order, OrderItem

# # Create tables
# Base.metadata.create_all(bind=engine)

# def create_app() -> FastAPI:
#     """Create FastAPI application with all configurations"""
    
#     app = FastAPI(
#         title="E-commerce API with Elasticsearch",
#         version="2.0.0",
#         description="A comprehensive e-commerce API with advanced search capabilities"
#     )

#     # CORS middleware
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=["http://localhost:5174", "http://localhost:5173"],
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )

#     # Create uploads directory if it doesn't exist
#     os.makedirs("uploads", exist_ok=True)
    
#     # Mount static files for serving uploaded images
#     app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
#     app.mount("/media", StaticFiles(directory="media"), name="media")

#     # Initialize Elasticsearch on startup
#     @app.on_event("startup")
#     async def startup_event():
#         try:
#             ElasticsearchService.initialize_index()
#             logger.info("Elasticsearch initialized successfully")
#         except Exception as e:
#             logger.error(f"Failed to initialize Elasticsearch: {str(e)}")
#             # Don't fail startup if Elasticsearch is not available
#             logger.warning("Application starting without Elasticsearch search capabilities")

    
#     # Include API routers
#     app.include_router(vender_auth.router, prefix="/api/vendor", tags=["vender_auth"])
#     app.include_router(vendor_orders.router, prefix="/api/vendor", tags=["vendor_orders"])
#     app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
#     app.include_router(categories.router, prefix="/api/v1", tags=["categories"])
#     app.include_router(specifications.router, prefix="/api/v1", tags=["specifications"])
#     app.include_router(pricing.router, prefix="/api/v1", tags=["pricing"])
#     app.include_router(products.router, prefix="/api/v1", tags=["products"])
#     app.include_router(cart.router, prefix="/api/v1", tags=["cart"])
#     app.include_router(addresses.router, prefix="/api/v1", tags=["addresses"])
#     app.include_router(orders.router, prefix="/api/v1", tags=["orders"])
#     app.include_router(vendor_orders.router, prefix="/api/vendor", tags=["vendor_orders"])
#     app.include_router(search.router, prefix="/api/v1", tags=["search"])  # New search router

#     @app.get("/")
#     async def root():
#         return {
#             "message": "E-commerce API with Elasticsearch",
#             "version": "2.0.0",
#             "status": "running",
#             "features": ["Authentication", "Products", "Cart", "Addresses", "Orders", "Advanced Search"]
#         }

#     @app.get("/health")
#     async def health_check():
#         # Check Elasticsearch health
#         try:
#             from config.elasticsearch import es_client
#             es_health = es_client.ping()
#         except:
#             es_health = False
            
#         return {
#             "status": "healthy",
#             "elasticsearch": "connected" if es_health else "disconnected"
#         }

#     return app

# app = create_app()

# if __name__ == "__main__":
#     uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)





# jagath  ELAKKIYA.COM

# Updated app.py - Add search router and initialize Elasticsearch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config.database import engine
from src.models import Base
from src.api.v1 import categories, products, auth, vender_auth, cart, addresses, orders, specifications, pricing, search, vendor_orders
from src.services.search import ElasticsearchService
import uvicorn
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import all models to ensure they're registered with SQLAlchemy
from src.models.customer import Customer
from src.models.otp import OTP
from src.models.address import CustomerAddress
from src.models.order import Order, OrderItem

# Create tables
Base.metadata.create_all(bind=engine)

from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

def create_app() -> FastAPI:
    """Create FastAPI application with all configurations"""

    app = FastAPI(
        title="E-commerce API with Elasticsearch",
        version="2.0.0",
        description="A comprehensive e-commerce API with advanced search capabilities"
    )

    # --- ADD PROXY HEADERS MIDDLEWARE HERE ---

    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["127.0.0.1"])

    # --- EXISTING CORS MIDDLEWARE ---
    app.add_middleware(
        CORSMiddleware,
        # Remember to update these to your actual domain for production!
        allow_origins=[
            "https://elakkiyaboutique.com",
            "https://www.elakkiyaboutique.com",
            "http://localhost:5174"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ... rest of your code (os.makedirs, mount, routers, etc.)











    # Create uploads directory if it doesn't exist
    os.makedirs("uploads", exist_ok=True)

    # Mount static files for serving uploaded images
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
    app.mount("/media", StaticFiles(directory="media"), name="media")

    # Initialize Elasticsearch on startup
    @app.on_event("startup")
    async def startup_event():
        try:
            ElasticsearchService.initialize_index()
            logger.info("Elasticsearch initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Elasticsearch: {str(e)}")
            # Don't fail startup if Elasticsearch is not available
            logger.warning("Application starting without Elasticsearch search capabilities")

    # Include API routers
    app.include_router(vender_auth.router, prefix="/api/vendor", tags=["vender_auth"])
    app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
    app.include_router(categories.router, prefix="/api/v1", tags=["categories"])
    app.include_router(specifications.router, prefix="/api/v1", tags=["specifications"])
    app.include_router(pricing.router, prefix="/api/v1", tags=["pricing"])
    app.include_router(products.router, prefix="/api/v1", tags=["products"])
    app.include_router(cart.router, prefix="/api/v1", tags=["cart"])
    app.include_router(addresses.router, prefix="/api/v1", tags=["addresses"])
    app.include_router(orders.router, prefix="/api/v1", tags=["orders"])
    app.include_router(vendor_orders.router, prefix="/api/vendor", tags=["vendor_orders"])
    app.include_router(search.router, prefix="/api/v1", tags=["search"])  # New search router

    @app.get("/")
    async def root():
        return {
            "message": "E-commerce API with Elasticsearch",
            "version": "2.0.0",
            "status": "running",
            "features": ["Authentication", "Products", "Cart", "Addresses", "Orders", "Advanced Search"]
        }

    @app.get("/health")
    async def health_check():
        # Check Elasticsearch health
        try:
            from config.elasticsearch import es_client
            es_health = es_client.ping()
        except:
            es_health = False

        return {
            "status": "healthy",
            "elasticsearch": "connected" if es_health else "disconnected"
        }

    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

# ==========================================
# ==========================================
# SETUP INSTRUCTIONS
# ==========================================

"""
🚀 ELASTICSEARCH SETUP GUIDE FOR YOUR E-COMMERCE PROJECT

1. INSTALL DEPENDENCIES
   Add to your requirements.txt:
   ```
   elasticsearch==8.11.0
   elasticsearch-dsl==8.11.0
   ```
   
   Then run:
   ```bash
   pip install elasticsearch==8.11.0 elasticsearch-dsl==8.11.0
   ```

2. SETUP ELASTICSEARCH SERVER

   Option A: Docker (Recommended for development)
   ```bash
   # Create docker-compose.yml with Elasticsearch service
   docker-compose up -d elasticsearch
   ```
   
   Option B: Local Installation
   ```bash
   # Download and install Elasticsearch 8.11.0
   # Start the service
   ```

3. ENVIRONMENT VARIABLES
   Add to your .env file:
   ```
   ELASTICSEARCH_HOST=localhost
   ELASTICSEARCH_PORT=9200
   ELASTICSEARCH_USERNAME=elastic
   ELASTICSEARCH_PASSWORD=changeme
   ELASTICSEARCH_USE_SSL=false
   ```

4. CREATE REQUIRED FILES
   Create these new files in your project:
   
   - config/elasticsearch.py (from first artifact)
   - src/search/documents.py (from first artifact)
   - src/search/service.py (from first artifact)
   - src/api/v1/search.py (from second artifact)
   - src/search/tasks.py (from second artifact)

5. UPDATE EXISTING FILES
   
   A. Update your app.py (see above)
   
   B. Add to src/models/product.py (at the bottom):
   ```python
   from sqlalchemy import event
   from src.search.tasks import SearchTasks
   import logging
   
   logger = logging.getLogger(__name__)
   
   @event.listens_for(Product, 'after_insert')
   def auto_index_on_insert(mapper, connection, target):
       try:
           SearchTasks.auto_index_product(target.product_id)
       except Exception as e:
           logger.error(f"Auto-indexing after insert failed: {str(e)}")
   
   @event.listens_for(Product, 'after_update')
   def auto_index_on_update(mapper, connection, target):
       try:
           SearchTasks.auto_index_product(target.product_id)
       except Exception as e:
           logger.error(f"Auto-indexing after update failed: {str(e)}")
   
   @event.listens_for(Product, 'after_delete')
   def auto_remove_on_delete(mapper, connection, target):
       try:
           SearchTasks.auto_remove_product(target.product_id)
       except Exception as e:
           logger.error(f"Auto-removal after delete failed: {str(e)}")
   ```

6. FRONTEND UPDATES
   
   A. Create src/services/api/searchAPI.js (from third artifact)
   B. Update your Header component (from third artifact)
   C. Create src/pages/SearchResults.jsx (from fourth artifact)
   D. Add route to your React router:
   ```javascript
   import SearchResults from './pages/SearchResults';
   
   // In your router setup:
   <Route path="/search" element={<SearchResults />} />
   ```

7. INITIAL DATA INDEXING
   After setup, index your existing products:
   ```bash
   # Make a POST request to reindex all products
   curl -X POST "http://65.1.248.179:8000/api/v1/search/reindex" \
        -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```
   
   Or use the frontend admin panel to trigger reindexing.

8. TESTING
   
   A. Test Elasticsearch connection:
   ```bash
   curl http://localhost:9200
   ```
   
   B. Test search API:
   ```bash
   curl "http://65.1.248.179:8000/api/v1/search?q=shirt&size=5"
   ```
   
   C. Test suggestions:
   ```bash
   curl "http://65.1.248.179:8000/api/v1/search/suggestions?q=sh"
   ```

9. ADVANCED FEATURES

   A. Search Analytics: Track search queries and results
   B. Synonyms: Add synonym filters for better matching
   C. Boost Rules: Boost certain products in search results
   D. Search Result Caching: Cache popular searches
   E. Real-time Indexing: Update index immediately on product changes

10. PRODUCTION CONSIDERATIONS

    A. Elasticsearch Cluster: Use multiple nodes for high availability
    B. Index Optimization: Regular index optimization and maintenance
    C. Monitoring: Set up Elasticsearch monitoring and alerting
    D. Security: Enable Elasticsearch security features
    E. Backup: Regular index backups

🎉 FEATURES YOU'LL GET:

✅ Fuzzy Search - Handles typos and misspellings
✅ Autocomplete/Suggestions - Real-time search suggestions
✅ Faceted Search - Filter by category, brand, price, etc.
✅ Advanced Sorting - Relevance, price, date, popularity
✅ Full-text Search - Search across name, description, specifications
✅ Real-time Indexing - Automatic index updates
✅ Performance - Fast search responses with pagination
✅ Analytics Ready - Track search performance and user behavior

📊 SEARCH CAPABILITIES:

- Multi-field search across product attributes
- Fuzzy matching with typo tolerance
- Boosted relevance scoring
- Category and brand filtering
- Price range filtering
- Stock status filtering
- Multiple sort options
- Pagination with facets
- Search suggestions with debouncing
- Real-time index updates

🔧 MAINTENANCE COMMANDS:

# Reindex all products
POST /api/v1/search/reindex

# Index single product
POST /api/v1/search/index-product/{product_id}

# Remove product from index
DELETE /api/v1/search/product/{product_id}

# Check Elasticsearch health
GET /health
"""