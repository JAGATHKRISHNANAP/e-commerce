
import sys
import os

try:
    print("Attempting imports...")
    from config.elasticsearch import es_client
    from src.services.search import ElasticsearchService
    print("Imports successful.")
except Exception as e:
    print(f"Import failed: {e}")
    sys.exit(1)

try:
    print("Checking Elasticsearch availability...")
    is_avail = ElasticsearchService.is_available()
    print(f"Elasticsearch Available: {is_avail}")
    
    # It should be False since we know port 9200 is down, but it shouldn't crash
    if is_avail:
        print("Warning: ES reported as available (unexpected if server is down)")
    else:
        print("Confirmed: ES is unavailable (expected fallback)")
        
except Exception as e:
    print(f"Service check failed: {e}")
    sys.exit(1)

print("Verification passed.")
