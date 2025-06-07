#!/usr/bin/env python3
"""
Local test script for the iframe compatibility processor.
This allows testing the Actor functionality without deploying to Apify.
"""

import asyncio
import json
from src.main import main
from apify import Actor

# Mock Actor input for testing
test_input = {
    "url": "https://example.com"  # Replace with URL you want to test
}

async def test_locally():
    """Test the Actor locally with mock input."""
    # Override Actor.get_input to return our test input
    original_get_input = Actor.get_input
    Actor.get_input = lambda: test_input
    
    # Override Actor.push_data to print results instead of storing
    results = []
    original_push_data = Actor.push_data
    Actor.push_data = lambda data: results.append(data)
    
    # Override Actor.exit to prevent actual exit
    Actor.exit = lambda: None
    
    try:
        await main()
        
        if results:
            print("\n=== RESULTS ===")
            for result in results:
                print(json.dumps(result, indent=2))
        else:
            print("No results generated")
            
    except Exception as e:
        print(f"Error during test: {e}")
    
    finally:
        # Restore original methods
        Actor.get_input = original_get_input
        Actor.push_data = original_push_data

if __name__ == "__main__":
    asyncio.run(test_locally())
