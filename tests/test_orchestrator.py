"""
Orchestrator Test Script
Quick tests for the semantic routing engine.
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from shared.orchestrator import get_orchestrator


async def test_orchestrator_async():
    """Test the Orchestrator with sample commands."""
    
    orchestrator = get_orchestrator()
    
    test_cases = [
        # Browser commands
        ("go to reddit.com", "browser", "navigate"),
        ("open youtube", "browser", "navigate"),
        ("search cheap GPUs on ebay", "browser", "search_site"),
        ("google how to make bread", "browser", "search"),
        
        # Todo commands
        ("add buy milk", "todo", "add"),
        ("remind me to call mom", "todo", "add"),
        ("todo finish report", "todo", "add"),
        
        # Read commands
        ("read this to me", "read", "speak"),
        ("summarize the article", "read", "summarize"),
        
        # Desktop commands
        ("type hello world", "desktop", "type"),
        ("click submit button", "desktop", "click"),
        ("screenshot", "desktop", "screenshot"),
        
        # System commands
        ("quit", "system", "quit"),
        ("restart", "system", "restart"),
    ]
    
    print("Orchestrator Test Results")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for command, expected_target, expected_action in test_cases:
        result = await orchestrator.process(command)
        
        target = result.get("target", "")
        action = result.get("action", "")
        method = result.get("method", "")
        confidence = result.get("confidence", 0)
        
        target_match = target == expected_target
        action_match = action == expected_action
        
        if target_match and action_match:
            status = "✅ PASS"
            passed += 1
        elif target_match:
            status = "⚠️ TARGET OK"
            passed += 0.5
        else:
            status = "❌ FAIL"
            failed += 1
        
        print(f"\n{status}")
        print(f"  Input:    '{command}'")
        print(f"  Expected: {expected_target}/{expected_action}")
        print(f"  Got:      {target}/{action}")
        print(f"  Method:   {method} (conf: {confidence:.0%})")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{len(test_cases)} passed, {failed} failed")
    
    print("\nRouting Stats:")
    stats = orchestrator.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

def test_orchestrator():
    asyncio.run(test_orchestrator_async())

if __name__ == "__main__":
    test_orchestrator()
