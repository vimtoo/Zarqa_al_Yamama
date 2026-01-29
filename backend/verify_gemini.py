
import asyncio
import logging
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings

from app.llm.client import GeminiClient, DryRunNetworkBlocked

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyGemini")

async def verify():
    print("🔒 Verifying Gemini API Auth Wiring...")
    
    enabled = settings.GEMINI_ENABLED
    has_key = bool(settings.GEMINI_API_KEY)
    
    print(f"   GEMINI_ENABLED: {enabled}")
    print(f"   GEMINI_DRY_RUN: {settings.GEMINI_DRY_RUN}")
    print(f"   GEMINI_API_KEY Linked: {'YES (Hidden)' if has_key else 'NO'}")
    
    if not enabled:
        print("⚠️  Gemini is DISABLED in config. Skipping network test.")
        print("   To enable: export GEMINI_ENABLED=true and GEMINI_API_KEY=...")
        return

    if not has_key:
        print("❌ FATAL: Gemini Enabled but NO API Key found.")
        print("   Please export GEMINI_API_KEY.")
        sys.exit(1)

    print("🚀 Attempting to initialize GeminiClient...")
    try:
        client = GeminiClient()
        response = await client.complete(
            prompt="Hello from Zarqa Al Yamama verification.",
            max_tokens=10
        )
        
        if response:
            print(f"✅ SUCCESS (LIVE): Received response: {response}")
        else:
            print("❌ FAILED: Received empty response. Check logs.")
            sys.exit(1)
            
    except DryRunNetworkBlocked:
        print("✅ SUCCESS (DRY RUN): Network call blocked by containment guard.")
    except Exception as e:
        print(f"❌ CONNECTION ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(verify())
