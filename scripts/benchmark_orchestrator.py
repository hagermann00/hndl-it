
import sys
import os
import time
import logging
import asyncio

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import mock setup BEFORE importing orchestrator
try:
    import ollama
except ImportError:
    import scripts.mock_ollama_setup

from shared.orchestrator import get_orchestrator

# Configure logging
logging.basicConfig(level=logging.ERROR)

async def benchmark_async():
    orchestrator = get_orchestrator()

    commands = [
        "Please open reddit.com",
        "I want to buy some milk",
        "Can you find cheap GPUs?",
        "Hey, check the system status",
        "I need to remember to call mom"
    ] * 5 # Increase load

    print(f"Running benchmark with {len(commands)} commands...")

    start_time = time.time()

    # Check if process is async
    if asyncio.iscoroutinefunction(orchestrator.process):
        print("Detected Async Orchestrator")
        # Run concurrently
        tasks = [orchestrator.process(cmd) for cmd in commands]
        await asyncio.gather(*tasks)
    else:
        print("Detected Sync Orchestrator")
        for cmd in commands:
            orchestrator.process(cmd)

    end_time = time.time()
    duration = end_time - start_time
    avg_time = duration / len(commands)

    print("\n" + "="*40)
    print(f"Total Time: {duration:.2f}s")
    print(f"Average Time per Request: {avg_time:.4f}s")
    print("="*40)

def main():
    if asyncio.iscoroutinefunction(get_orchestrator().process):
        asyncio.run(benchmark_async())
    else:
        # Sync wrapper
        asyncio.run(benchmark_async())

if __name__ == "__main__":
    main()
