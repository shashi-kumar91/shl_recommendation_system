#!/usr/bin/env python3
"""
Test script to verify API functionality.
"""
import requests
import json
import sys


def test_health(base_url: str):
    """Test health endpoint."""
    print("\n" + "="*80)
    print("Testing Health Endpoint")
    print("="*80)
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200 and response.json().get("status") == "healthy":
            print("✅ Health check passed")
            return True
        else:
            print("❌ Health check failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_recommend(base_url: str, query: str):
    """Test recommend endpoint."""
    print("\n" + "="*80)
    print(f"Testing Recommend Endpoint")
    print(f"Query: {query[:100]}...")
    print("="*80)
    
    try:
        response = requests.post(
            f"{base_url}/recommend",
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            if "query" not in data or "recommendations" not in data:
                print("❌ Invalid response structure")
                return False
            
            recommendations = data["recommendations"]
            print(f"Number of recommendations: {len(recommendations)}")
            
            if not (5 <= len(recommendations) <= 10):
                print(f"⚠️  Warning: Expected 5-10 recommendations, got {len(recommendations)}")
            
            # Validate first recommendation
            if recommendations:
                first = recommendations[0]
                print(f"\nFirst recommendation:")
                print(f"  Name: {first.get('name', 'N/A')}")
                print(f"  URL: {first.get('url', 'N/A')}")
                print(f"  Duration: {first.get('duration', 'N/A')} min")
                print(f"  Types: {', '.join(first.get('test_type', []))}")
                
                # Validate required fields
                required_fields = ['name', 'url', 'description', 'duration', 
                                 'adaptive_support', 'remote_support', 'test_type']
                
                missing = [f for f in required_fields if f not in first]
                if missing:
                    print(f"⚠️  Warning: Missing fields: {missing}")
                else:
                    print("✅ All required fields present")
            
            print("\n✅ Recommend endpoint test passed")
            return True
        else:
            print(f"❌ Request failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_error_handling(base_url: str):
    """Test error handling."""
    print("\n" + "="*80)
    print("Testing Error Handling")
    print("="*80)
    
    # Test empty query
    print("\nTest 1: Empty query")
    try:
        response = requests.post(
            f"{base_url}/recommend",
            json={"query": ""},
            timeout=5
        )
        if response.status_code == 400:
            print("✅ Empty query rejected correctly")
        else:
            print(f"⚠️  Expected 400, got {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test missing query
    print("\nTest 2: Missing query field")
    try:
        response = requests.post(
            f"{base_url}/recommend",
            json={},
            timeout=5
        )
        if response.status_code == 400:
            print("✅ Missing query rejected correctly")
        else:
            print(f"⚠️  Expected 400, got {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test invalid JSON
    print("\nTest 3: Invalid JSON")
    try:
        response = requests.post(
            f"{base_url}/recommend",
            data="invalid json",
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        if response.status_code in [400, 500]:
            print("✅ Invalid JSON handled")
        else:
            print(f"⚠️  Expected 400/500, got {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all tests."""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:5000"
    
    print(f"\nTesting API at: {base_url}")
    
    # Test health
    health_ok = test_health(base_url)
    
    if not health_ok:
        print("\n❌ Health check failed. Make sure the server is running.")
        sys.exit(1)
    
    # Test recommend with various queries
    test_queries = [
        "I am hiring for Java developers who can also collaborate effectively with my business teams. Looking for an assessment that can be completed in 40 minutes.",
        "Looking to hire mid-level professionals who are proficient in Python, SQL and JavaScript. Need an assessment package with max duration of 60 minutes.",
        "Content Writer required, expert in English and SEO.",
        "Senior data analyst with SQL and Python expertise"
    ]
    
    results = []
    for query in test_queries:
        result = test_recommend(base_url, query)
        results.append(result)
    
    # Test error handling
    test_error_handling(base_url)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Health Check: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"Recommend Tests: {sum(results)}/{len(results)} passed")
    
    if health_ok and all(results):
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()