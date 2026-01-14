"""
Test Orchestrator Retrieval
Simulates a user command "recall Y-IT Research" to verify Airweave triggering.
"""
import sys
import os
import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from shared.orchestrator import Orchestrator

# Mock Airweave Client to avoid needing the real backend for this unit test
import shared.airweave_client
class MockAirweaveClient:
    def search(self, query, limit=5, **kwargs):
        return [
            shared.airweave_client.AirweaveResult(
                score=0.9, title="Mock Result", content="Content", 
                source_name="mock", entity_id="1", metadata={}
            )
        ]
    def to_a2ui(self, results):
        return {"type": "List", "children": []}

shared.airweave_client.get_airweave_client = lambda: MockAirweaveClient()

def test_retrieval():
    orch = Orchestrator()
    
    # Test regex triggering
    cmd = "recall Y-IT Research"
    result = orch.process(cmd)
    
    print(f"Command: {cmd}")
    print(f"Result Target: {result['target']}")
    print(f"Result Action: {result['action']}")
    print(f"Method: {result['method']}")
    
    if result['target'] == 'floater' and result['action'] == 'render_a2ui':
        print("✅ SUCCESS: Retrieval command routed to A2UI render!")
    else:
        print("❌ FAILURE: Incorrect routing")

if __name__ == "__main__":
    test_retrieval()
