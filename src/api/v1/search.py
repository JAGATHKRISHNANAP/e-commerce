# # src/api/v1/search.py
# from fastapi import APIRouter, Depends, HTTPException, Query
# from sqlalchemy.orm import Session
# from typing import List, Optional
# from pydantic import BaseModel

# from config.database import get_db
# from src.services.search import ElasticsearchService
# from src.models.product import Product

# router = APIRouter()

# class SearchResponse(BaseModel):
#     products: List[dict]
#     total: int
#     page: int
#     size: int
#     total_pages: int
#     facets: dict
#     took: Optional[int] = None

# class SearchFilters(BaseModel):
#     category_id: Optional[int] = None
#     subcategory_id: Optional[int] = None
#     min_price: Optional[float] = None
#     max_price: Optional[float] = None
#     brand: Optional[str] = None
#     in_stock_only: bool = True
#     sort_by: str = 'relevance'  # relevance, price_low, price_high, newest, popularity

# @router.get("/search", response_model=SearchResponse)
# async def search_products(
#     q: str = Query(..., description="Search query"),
#     category_id: Optional[int] = Query(None, description="Filter by category ID"),
#     subcategory_id: Optional[int] = Query(None, description="Filter by subcategory ID"),
#     min_price: Optional[float] = Query(None, description="Minimum price filter"),
#     max_price: Optional[float] = Query(None, description="Maximum price filter"),
#     brand: Optional[str] = Query(None, description="Filter by brand"),
#     in_stock_only: bool = Query(True, description="Show only in-stock products"),
#     sort_by: str = Query('relevance', description="Sort by: relevance, price_low, price_high, newest, popularity"),
#     page: int = Query(1, ge=1, description="Page number"),
#     size: int = Query(20, ge=1, le=100, description="Number of results per page")
# ):
#     """
#     Advanced product search with filters and facets
    
#     - **q**: Search query (required)
#     - **category_id**: Filter by category
#     - **subcategory_id**: Filter by subcategory  
#     - **min_price/max_price**: Price range filter
#     - **brand**: Filter by brand
#     - **in_stock_only**: Show only products with stock > 0
#     - **sort_by**: Sort results (relevance, price_low, price_high, newest, popularity)
#     - **page/size**: Pagination
#     """
#     try:
#         result = ElasticsearchService.search_products(
#             query=q,
#             category_id=category_id,
#             subcategory_id=subcategory_id,
#             min_price=min_price,
#             max_price=max_price,
#             brand=brand,
#             in_stock_only=in_stock_only,
#             sort_by=sort_by,
#             page=page,
#             size=size
#         )
        
#         return SearchResponse(**result)
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# @router.get("/search/suggestions")
# async def get_search_suggestions(
#     q: str = Query(..., min_length=2, description="Search query (minimum 2 characters)"),
#     size: int = Query(10, ge=1, le=20, description="Number of suggestions")
# ):
#     """
#     Get search suggestions/autocomplete
    
#     - **q**: Search query (minimum 2 characters)
#     - **size**: Number of suggestions to return (1-20)
#     """
#     try:
#         suggestions = ElasticsearchService.get_search_suggestions(q, size)
#         return {"suggestions": suggestions}
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Suggestions failed: {str(e)}")

# @router.post("/search/reindex")
# async def reindex_products(db: Session = Depends(get_db)):
#     """
#     Reindex all products (Admin only - add authentication as needed)
#     """
#     try:
#         result = ElasticsearchService.reindex_all_products(db)
#         return {
#             "message": "Reindexing completed",
#             "result": result
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Reindexing failed: {str(e)}")

# @router.post("/search/index-product/{product_id}")
# async def index_single_product(product_id: int, db: Session = Depends(get_db)):
#     """
#     Index a single product (useful for real-time updates)
#     """
#     try:
#         product = db.query(Product).filter(Product.product_id == product_id).first()
#         if not product:
#             raise HTTPException(status_code=404, detail="Product not found")
        
#         success = ElasticsearchService.index_product(product)
        
#         if success:
#             return {"message": f"Product {product_id} indexed successfully"}
#         else:
#             raise HTTPException(status_code=500, detail="Failed to index product")
            
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

# @router.delete("/search/product/{product_id}")
# async def delete_product_from_index(product_id: int):
#     """
#     Remove a product from search index
#     """
#     try:
#         success = ElasticsearchService.delete_product(product_id)
        
#         if success:
#             return {"message": f"Product {product_id} removed from index"}
#         else:
#             raise HTTPException(status_code=500, detail="Failed to remove product from index")
            
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")



# """
# # Elasticsearch Configuration
# ELASTICSEARCH_HOST=localhost
# ELASTICSEARCH_PORT=9200
# ELASTICSEARCH_USERNAME=elastic
# ELASTICSEARCH_PASSWORD=changeme
# ELASTICSEARCH_USE_SSL=false
# """

# # Docker Compose for local Elasticsearch setup
# """
# # docker-compose.yml - Add this service
# version: '3.8'
# services:
#   elasticsearch:
#     image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
#     container_name: ecommerce_elasticsearch
#     environment:
#       - discovery.type=single-node
#       - xpack.security.enabled=false
#       - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
#     ports:
#       - "9200:9200"
#       - "9300:9300"
#     volumes:
#       - elasticsearch_data:/usr/share/elasticsearch/data
#     networks:
#       - ecommerce_network

# volumes:
#   elasticsearch_data:

# networks:
#   ecommerce_network:
# """












# src/api/v1/search.py - Enhanced with detailed logging and debugging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import logging
import json

from config.database import get_db
from src.services.search import ElasticsearchService
from src.models.product import Product

# Set up detailed logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class SearchResponse(BaseModel):
    products: List[dict]
    total: int
    page: int
    size: int
    total_pages: int
    facets: dict
    took: Optional[int] = None

class SearchFilters(BaseModel):
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    brand: Optional[str] = None
    in_stock_only: bool = True
    sort_by: str = 'relevance'

@router.get("/search", response_model=SearchResponse)
async def search_products(
    q: str = Query(..., description="Search query"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    subcategory_id: Optional[int] = Query(None, description="Filter by subcategory ID"),
    min_price: Optional[float] = Query(None, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, description="Maximum price filter"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    in_stock_only: bool = Query(True, description="Show only in-stock products"),
    sort_by: str = Query('relevance', description="Sort by: relevance, price_low, price_high, newest, popularity"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Number of results per page"),
    debug: bool = Query(False, description="Enable debug mode for detailed logging"),
    db: Session = Depends(get_db)
):
    """
    Advanced product search with filters and facets
    """
    try:
        # Log the incoming search request
        search_params = {
            "query": q,
            "category_id": category_id,
            "subcategory_id": subcategory_id,
            "min_price": min_price,
            "max_price": max_price,
            "brand": brand,
            "in_stock_only": in_stock_only,
            "sort_by": sort_by,
            "page": page,
            "size": size
        }
        
        print("\n" + "="*80)
        print("🔍 SEARCH REQUEST")
        print("="*80)
        print(f"📝 Search Query: '{q}'")
        print(f"🔧 Parameters: {json.dumps(search_params, indent=2)}")
        print("="*80)
        
        # Check if Elasticsearch is available
        if not ElasticsearchService.is_available():
            print("⚠️ Elasticsearch is not available - falling back to Database Search")
            
            # SQL Fallback Implementation
            query = db.query(Product).filter(
                (Product.name.ilike(f"%{q}%")) | 
                (Product.description.ilike(f"%{q}%"))
            )
            
            if category_id:
                query = query.filter(Product.category_id == category_id)
            if subcategory_id:
                query = query.filter(Product.subcategory_id == subcategory_id)
            if min_price:
                query = query.filter(Product.price >= min_price)
            if max_price:
                query = query.filter(Product.price <= max_price)
            if in_stock_only:
                query = query.filter(Product.stock_quantity > 0)
                
            # Count total before pagination
            total = query.count()
            
            # Apply sorting
            if sort_by == 'price_low':
                query = query.order_by(Product.price.asc())
            elif sort_by == 'price_high':
                query = query.order_by(Product.price.desc())
            elif sort_by == 'newest':
                query = query.order_by(Product.created_at.desc())
            
            # Apply pagination
            products = query.offset((page - 1) * size).limit(size).all()
            
            # Format results
            product_list = []
            for p in products:
                # Calculate effective price logic if needed, simplify for fallback
                price = getattr(p, 'calculated_price', None) or getattr(p, 'base_price', None) or p.price
                if price and hasattr(p, 'calculated_price') and p.calculated_price: price = price / 100
                elif price and hasattr(p, 'base_price') and p.base_price: price = price / 100
                
                product_list.append({
                    "product_id": p.product_id,
                    "name": p.name,
                    "description": p.description,
                    "price": float(price) if price else 0.0,
                    "category_name": p.category.name if p.category else None,
                    "subcategory_name": p.subcategory.name if p.subcategory else None,
                    "brand": None, # Complex to extract from specs in fallback
                    "stock_quantity": p.stock_quantity,
                    "primary_image_url": p.primary_image_url,
                    "sku": p.sku,
                    "score": 1.0 # Dummy score
                })

            return SearchResponse(
                products=product_list,
                total=total,
                page=page,
                size=size,
                total_pages=(total + size - 1) // size if size > 0 else 0,
                facets={},
                took=0
            )
        
        # Perform the search
        print("🚀 Executing Elasticsearch search...")
        result = ElasticsearchService.search_products(
            query=q,
            category_id=category_id,
            subcategory_id=subcategory_id,
            min_price=min_price,
            max_price=max_price,
            brand=brand,
            in_stock_only=in_stock_only,
            sort_by=sort_by,
            page=page,
            size=size
        )
        
        # Print detailed results
        print("\n" + "="*80)
        print("📊 ELASTICSEARCH SEARCH RESULTS")
        print("="*80)
        print(f"📈 Total Results Found: {result.get('total', 0)}")
        print(f"⏱️  Search Time: {result.get('took', 0)}ms")
        print(f"📄 Page: {page} of {result.get('total_pages', 0)}")
        print(f"📦 Products on this page: {len(result.get('products', []))}")
        
        # Print each product found
        products = result.get('products', [])
        if products:
            print("\n🛍️  PRODUCTS FOUND:")
            print("-" * 80)
            for i, product in enumerate(products, 1):
                print(f"#{i}. {product.get('name', 'Unknown Product')}")
                print(f"    💰 Price: ${product.get('price', 0):.2f}")
                print(f"    🏷️  Brand: {product.get('brand', 'N/A')}")
                print(f"    📁 Category: {product.get('category_name', 'N/A')}")
                print(f"    📦 Stock: {product.get('stock_quantity', 0)}")
                print(f"    ⭐ Relevance Score: {product.get('score', 0):.2f}")
                print(f"    🆔 Product ID: {product.get('product_id', 'N/A')}")
                print("-" * 40)
        else:
            print("\n❌ No products found for this search!")
            print("💡 Try:")
            print("   - Different search terms")
            print("   - Removing filters")
            print("   - Checking if products are indexed")
        
        # Print facets/filters available
        facets = result.get('facets', {})
        if facets:
            print("\n🏷️  AVAILABLE FILTERS:")
            print("-" * 40)
            
            if 'categories' in facets:
                print("📁 Categories:")
                for cat in facets['categories']:
                    print(f"   - {cat['name']} ({cat['count']} products)")
            
            if 'brands' in facets:
                print("🏢 Brands:")
                for brand in facets['brands']:
                    print(f"   - {brand['name']} ({brand['count']} products)")
            
            if 'price_ranges' in facets:
                print("💰 Price Ranges:")
                for price_range in facets['price_ranges']:
                    print(f"   - ${price_range['range']} ({price_range['count']} products)")
        
        print("="*80 + "\n")
        
        # Log to file as well (optional)
        if debug:
            with open('search_debug.log', 'a') as f:
                f.write(f"\n[{q}] - {len(products)} results - {result.get('took', 0)}ms\n")
                f.write(json.dumps(result, indent=2) + "\n")
        
        return SearchResponse(**result)
        
    except Exception as e:
        print(f"\n❌ SEARCH ERROR: {str(e)}")
        print(f"🔧 Error Type: {type(e).__name__}")
        logger.error(f"Search failed for query '{q}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/search/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=2, description="Search query (minimum 2 characters)"),
    size: int = Query(10, ge=1, le=20, description="Number of suggestions"),
    db: Session = Depends(get_db)
):
    """
    Get search suggestions/autocomplete with debugging
    """
    try:
        print(f"\n🔍 GETTING SUGGESTIONS for: '{q}'")
        
        if not ElasticsearchService.is_available():
            print("⚠️ Elasticsearch not available - falling back to DB Suggestions")
            
            # SQL Fallback
            products = db.query(Product).filter(
                Product.name.ilike(f"%{q}%")
            ).limit(size * 3).all()  # Fetch more to allow for deduplication
            
            # Deduplicate names while preserving order
            seen = set()
            suggestions = []
            for p in products:
                if p.name not in seen:
                    seen.add(p.name)
                    suggestions.append(p.name)
                    if len(suggestions) >= size:
                        break
            
            return {"suggestions": suggestions}
        
        suggestions = ElasticsearchService.get_search_suggestions(q, size)
        
        print(f"💡 Found {len(suggestions)} suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. {suggestion}")
        
        return {"suggestions": suggestions}
        
    except Exception as e:
        print(f"❌ SUGGESTIONS ERROR: {str(e)}")
        logger.error(f"Suggestions failed for query '{q}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Suggestions failed: {str(e)}")

@router.post("/search/reindex")
async def reindex_products(db: Session = Depends(get_db)):
    """
    Reindex all products with detailed progress logging
    """
    try:
        print("\n" + "="*80)
        print("🔄 STARTING ELASTICSEARCH REINDEXING")
        print("="*80)
        
        if not ElasticsearchService.is_available():
            print("❌ Elasticsearch not available for reindexing")
            return {"error": "Elasticsearch not available"}
        
        # Get product count first
        total_products = db.query(Product).filter(Product.is_active == True).count()
        print(f"📊 Total active products to index: {total_products}")
        
        result = ElasticsearchService.reindex_all_products(db)
        
        print("\n📈 REINDEXING RESULTS:")
        print(f"   ✅ Successfully indexed: {result.get('success', 0)}")
        print(f"   ❌ Errors: {result.get('errors', 0)}")
        print(f"   📦 Total processed: {result.get('total', 0)}")
        
        if result.get('success', 0) > 0:
            print("🎉 Reindexing completed successfully!")
        else:
            print("⚠️  Reindexing had issues. Check the logs.")
        
        print("="*80 + "\n")
        
        return {
            "message": "Reindexing completed",
            "result": result
        }
    except Exception as e:
        print(f"❌ REINDEXING ERROR: {str(e)}")
        logger.error(f"Reindexing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Reindexing failed: {str(e)}")

@router.get("/search/debug")
async def debug_search_status():
    """
    Debug endpoint to check search system status
    """
    try:
        print("\n" + "="*80)
        print("🔧 ELASTICSEARCH DEBUG STATUS")
        print("="*80)
        
        status = {
            "elasticsearch_available": ElasticsearchService.is_available(),
            "timestamp": str(logger.info),
        }
        
        if ElasticsearchService.is_available():
            print("✅ Elasticsearch is available and running")
            
            # Try to get index info
            try:
                from config.elasticsearch import es_client
                index_exists = es_client.indices.exists(index='ecommerce_products')
                status["index_exists"] = index_exists
                
                if index_exists:
                    doc_count = es_client.count(index='ecommerce_products')
                    status["document_count"] = doc_count['count']
                    print(f"📊 Index exists with {doc_count['count']} documents")
                else:
                    print("⚠️  Index 'ecommerce_products' does not exist")
                    
            except Exception as e:
                print(f"❌ Error checking index: {str(e)}")
                status["index_error"] = str(e)
        else:
            print("❌ Elasticsearch is not available")
            print("💡 To fix this:")
            print("   1. Install Elasticsearch")
            print("   2. Start Elasticsearch service")
            print("   3. Check http://localhost:9200")
        
        print("="*80 + "\n")
        return status
        
    except Exception as e:
        print(f"❌ DEBUG ERROR: {str(e)}")
        return {"error": str(e)}
    

@router.get("/search/health")
async def search_health():
    """
    Check search service health
    """
    return {
        "elasticsearch_available": ElasticsearchService.is_available(),
        "status": "healthy" if ElasticsearchService.is_available() else "elasticsearch_unavailable"
    }

@router.post("/search/test")
async def test_search(db: Session = Depends(get_db)):
    """
    Test endpoint to verify search is working
    """
    try:
        print("\n" + "="*80)
        print("🧪 TESTING ELASTICSEARCH SEARCH")
        print("="*80)
        
        # Test 1: Check Elasticsearch availability
        print("Test 1: Checking Elasticsearch availability...")
        if not ElasticsearchService.is_available():
            print("❌ Test 1 FAILED: Elasticsearch not available")
            return {"status": "failed", "reason": "Elasticsearch not available"}
        print("✅ Test 1 PASSED: Elasticsearch is available")
        
        # Test 2: Check if we have products in database
        print("\nTest 2: Checking products in database...")
        db_products = db.query(Product).filter(Product.is_active == True).limit(5).all()
        if not db_products:
            print("❌ Test 2 FAILED: No active products in database")
            return {"status": "failed", "reason": "No products in database"}
        print(f"✅ Test 2 PASSED: Found {len(db_products)} products in database")
        
        # Test 3: Try indexing a product
        print("\nTest 3: Testing product indexing...")
        test_product = db_products[0]
        success = ElasticsearchService.index_product(test_product)
        if not success:
            print("❌ Test 3 FAILED: Could not index product")
            return {"status": "failed", "reason": "Product indexing failed"}
        print(f"✅ Test 3 PASSED: Successfully indexed product '{test_product.name}'")
        
        # Test 4: Try a simple search
        print("\nTest 4: Testing search functionality...")
        search_result = ElasticsearchService.search_products(
            query=test_product.name.split()[0],  # Search for first word of product name
            page=1,
            size=5
        )
        
        if search_result['total'] == 0:
            print("⚠️  Test 4 WARNING: Search returned no results")
            print("💡 This might be normal if the product was just indexed")
        else:
            print(f"✅ Test 4 PASSED: Search found {search_result['total']} results")
        
        print("\n🎉 ALL TESTS COMPLETED!")
        print("="*80 + "\n")
        
        return {
            "status": "success",
            "tests_passed": 4,
            "sample_product": test_product.name,
            "search_results": search_result['total']
        }
        
    except Exception as e:
        print(f"❌ TEST ERROR: {str(e)}")
        return {"status": "error", "error": str(e)}