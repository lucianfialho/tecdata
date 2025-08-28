#!/usr/bin/env python3
"""Basic setup test without database dependency."""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test basic imports work."""
    print("Testing basic imports...")
    
    try:
        from config.settings import settings
        print("✓ Settings imported successfully")
        
        from src.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Logger working correctly")
        print("✓ Logger working")
        
        from src.utils.http_client import HTTPClient
        print("✓ HTTP Client imported")
        
        # Test settings
        print(f"✓ Environment: {settings.environment}")
        print(f"✓ API URL: {settings.api.tecmundo_full_url}")
        print(f"✓ Database URL: {settings.database.url}")
        
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_http_client():
    """Test HTTP client can make basic requests."""
    print("\nTesting HTTP client...")
    
    try:
        from src.utils.http_client import HTTPClient
        
        with HTTPClient() as client:
            # Test with a simple HTTP request
            response = client.get("https://httpbin.org/get", timeout=10)
            print(f"✓ HTTP request successful: {response.status_code}")
            return True
            
    except Exception as e:
        print(f"✗ HTTP client test failed: {e}")
        return False

def test_tecmundo_api():
    """Test Tecmundo API accessibility."""
    print("\nTesting Tecmundo API...")
    
    try:
        from config.settings import settings
        from src.utils.http_client import HTTPClient
        
        with HTTPClient() as client:
            url = settings.api.tecmundo_full_url
            print(f"Testing URL: {url}")
            
            response = client.get(url, timeout=10)
            print(f"✓ Tecmundo API accessible: {response.status_code}")
            
            # Try to parse JSON
            data = response.json()
            print(f"✓ JSON response received, type: {type(data)}")
            
            if isinstance(data, list):
                print(f"✓ Response is list with {len(data)} items")
            elif isinstance(data, dict):
                print(f"✓ Response is dict with keys: {list(data.keys())[:5]}")
            
            return True
            
    except Exception as e:
        print(f"✗ Tecmundo API test failed: {e}")
        return False

def main():
    """Run all basic tests."""
    print("=" * 60)
    print("Termômetro de Tecnologia - Basic Setup Test")
    print("=" * 60)
    
    tests = [
        ("Basic Imports", test_imports),
        ("HTTP Client", test_http_client),
        ("Tecmundo API", test_tecmundo_api),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n[{passed + 1}/{total}] {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} - PASSED")
            else:
                print(f"✗ {test_name} - FAILED")
        except Exception as e:
            print(f"✗ {test_name} - ERROR: {e}")
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic tests passed!")
        print("Environment is ready for database setup.")
    else:
        print("❌ Some tests failed. Check the output above.")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)