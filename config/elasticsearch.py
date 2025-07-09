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