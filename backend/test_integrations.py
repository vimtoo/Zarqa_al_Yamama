#!/usr/bin/env python3
"""
Test script to verify all external integrations are working.
Run this to validate API connections and credentials.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()


async def test_polygon_api():
    """Test Polygon.io API connection"""
    print("\n" + "="*60)
    print("Testing Polygon.io API...")
    print("="*60)
    
    from app.agents.temporal_analyst import PolygonClient
    
    client = PolygonClient()
    
    if not client.api_key:
        print("❌ Polygon API key not configured")
        return False
    
    # Test getting previous close for SPY
    prev_close = await client.get_previous_close("SPY")
    
    if prev_close:
        print(f"✅ Polygon.io Connected!")
        print(f"   SPY Previous Close: ${prev_close.get('c', 'N/A')}")
        return True
    else:
        print("❌ Polygon API call failed")
        return False


async def test_newsdata_api():
    """Test NewsData.io API connection"""
    print("\n" + "="*60)
    print("Testing NewsData.io API...")
    print("="*60)
    
    from app.agents.context_interpreter import NewsDataClient
    
    client = NewsDataClient()
    
    if not client.api_key:
        print("❌ NewsData.io API key not configured")
        return False
    
    # Test getting news
    news = await client.get_news(query="technology", category="business")
    
    if news:
        print(f"✅ NewsData.io Connected!")
        print(f"   Fetched {len(news)} articles")
        if news:
            print(f"   Sample: {news[0].get('title', 'N/A')[:60]}...")
        return True
    else:
        print("❌ NewsData.io API call failed or returned no results")
        return False


async def test_openrouter_api():
    """Test OpenRouter LLM API"""
    print("\n" + "="*60)
    print("Testing OpenRouter API...")
    print("="*60)
    
    from app.llm.client import OpenRouterClient
    
    client = OpenRouterClient()
    
    if not client.api_key:
        print("❌ OpenRouter API key not configured")
        return False
    
    # Test simple completion
    response = await client.complete(
        prompt="Say 'Hello from Zarqa al Yamama!' in exactly those words.",
        temperature=0.1,
        max_tokens=50
    )
    
    if response:
        print(f"✅ OpenRouter Connected!")
        print(f"   Response: {response[:100]}...")
        return True
    else:
        print("❌ OpenRouter API call failed")
        return False


async def test_deepseek_api():
    """Test DeepSeek LLM API"""
    print("\n" + "="*60)
    print("Testing DeepSeek API...")
    print("="*60)
    
    from app.llm.client import DeepSeekClient
    
    client = DeepSeekClient()
    
    if not client.api_key:
        print("❌ DeepSeek API key not configured")
        return False
    
    # Test simple completion
    response = await client.complete(
        prompt="What is 2+2? Reply with just the number.",
        temperature=0.1,
        max_tokens=10
    )
    
    if response:
        print(f"✅ DeepSeek Connected!")
        print(f"   Response: {response}")
        return True
    else:
        print("❌ DeepSeek API call failed")
        return False


def test_neo4j_connection():
    """Test Neo4j Aura connection"""
    print("\n" + "="*60)
    print("Testing Neo4j Aura Connection...")
    print("="*60)
    
    from app.db.neo4j import get_neo4j_graph
    
    try:
        graph = get_neo4j_graph()
        
        if graph.health_check():
            print(f"✅ Neo4j Connected!")
            stats = graph.get_graph_stats()
            print(f"   Database: {stats.get('database', 'N/A')}")
            print(f"   Actors: {stats.get('actors', 0)}")
            print(f"   Themes: {stats.get('themes', 0)}")
            print(f"   Events: {stats.get('events', 0)}")
            return True
        else:
            print("❌ Neo4j health check failed")
            return False
            
    except Exception as e:
        print(f"❌ Neo4j Connection Error: {str(e)}")
        return False


def test_qdrant_connection():
    """Test Qdrant Cloud connection"""
    print("\n" + "="*60)
    print("Testing Qdrant Cloud Connection...")
    print("="*60)
    
    from app.db.qdrant import get_qdrant_db
    
    try:
        db = get_qdrant_db()
        
        if db.health_check():
            print(f"✅ Qdrant Connected!")
            stats = db.get_collection_stats()
            print(f"   Collection: {stats.get('name', 'N/A')}")
            print(f"   Points: {stats.get('points_count', 0)}")
            print(f"   Status: {stats.get('status', 'N/A')}")
            
            # Test embedding generation
            test_text = "This is a test embedding for Zarqa al Yamama."
            embedding = db.generate_embedding(test_text)
            print(f"   Embedding dimension: {len(embedding)}")
            
            return True
        else:
            print("❌ Qdrant health check failed")
            return False
            
    except Exception as e:
        print(f"❌ Qdrant Connection Error: {str(e)}")
        return False


async def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*60)
    print("ZARQA AL YAMAMA - Integration Tests")
    print("="*60)
    
    results = {}
    
    # Test Polygon.io
    results['Polygon.io'] = await test_polygon_api()
    
    # Test NewsData.io
    results['NewsData.io'] = await test_newsdata_api()
    
    # Test OpenRouter
    results['OpenRouter'] = await test_openrouter_api()
    
    # Test DeepSeek
    results['DeepSeek'] = await test_deepseek_api()
    
    # Test Neo4j (sync)
    results['Neo4j'] = test_neo4j_connection()
    
    # Test Qdrant (sync)
    results['Qdrant'] = test_qdrant_connection()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for service, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {service}: {'PASSED' if status else 'FAILED'}")
        if status:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All integrations working correctly!")
    else:
        print(f"\n⚠️  {failed} integration(s) need attention.")
    
    return results


if __name__ == "__main__":
    asyncio.run(run_all_tests())
