"""
Simple test script to verify NATS setup and basic agent communication
"""

import asyncio
import sys


async def test_nats_connection():
    """Test basic NATS connectivity"""
    print("Testing NATS connection...")
    try:
        import nats
        nc = await nats.connect("nats://localhost:4222", connect_timeout=3)
        print("✓ Connected to NATS successfully")
        await nc.close()
        return True
    except ImportError:
        print("✗ nats-py not installed. Run: pip install nats-py")
        return False
    except Exception as error:
        print(f"✗ Could not connect to NATS: {error}")
        print("  Make sure NATS server is running on localhost:4222")
        print("  Run: docker run -p 4222:4222 nats:latest")
        return False


async def test_lm_studio():
    """Test LM Studio connectivity"""
    print("\nTesting LM Studio connection...")
    try:
        from openai import OpenAI
        client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio")
        
        # Try a simple completion
        response = client.chat.completions.create(
            model="local-model",  # Will use whatever model is loaded
            messages=[{"role": "user", "content": "Say 'test'"}],
            max_tokens=5,
            timeout=5
        )
        print("✓ Connected to LM Studio successfully")
        return True
    except ImportError:
        print("✗ openai package not installed")
        return False
    except Exception as error:
        print(f"✗ Could not connect to LM Studio: {error}")
        print("  Make sure LM Studio is running on localhost:1234")
        print("  And a model is loaded")
        return False


async def test_agent_creation():
    """Test creating a NATS-enabled agent"""
    print("\nTesting agent creation...")
    try:
        from nats_ooda_agent import NATSOODAAgent, tools
        
        agent = NATSOODAAgent(
            name="Test-Agent",
            instructions="You are a test agent",
            model="qwen/qwen3-32b",
            tools=tools
        )
        print("✓ Agent created successfully")
        return True
    except ImportError as error:
        print(f"✗ Import error: {error}")
        return False
    except Exception as error:
        print(f"✗ Could not create agent: {error}")
        return False


async def main():
    """Run all tests"""
    print("="*60)
    print("NATS Agent Communication System - Setup Test")
    print("="*60)
    
    tests = [
        test_nats_connection(),
        test_lm_studio(),
        test_agent_creation()
    ]
    
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    print("\n" + "="*60)
    print("Test Results:")
    print("="*60)
    
    all_passed = all(r is True for r in results if not isinstance(r, Exception))
    
    if all_passed:
        print("✓ All tests passed! System is ready.")
        print("\nNext steps:")
        print("  1. Run the demo: python demo_nats_agents.py")
        print("  2. Create your own NATS-enabled agents")
        print("  3. Read README_NATS.md for details")
        return 0
    else:
        print("✗ Some tests failed. Please fix the issues above.")
        print("\nTroubleshooting:")
        print("  - Install deps: pip install nats-py openai")
        print("  - Start NATS: docker run -p 4222:4222 nats:latest")
        print("  - Start LM Studio and load a model")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

