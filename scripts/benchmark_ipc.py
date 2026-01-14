import sys
import os
import time
import threading
import json
import statistics
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.agent_base import BaseAgent
from shared.ipc import send_command, IPC_DIR

# Ensure IPC directory exists
if not os.path.exists(IPC_DIR):
    os.makedirs(IPC_DIR, exist_ok=True)

class BenchmarkAgent(BaseAgent):
    def __init__(self):
        super().__init__("benchmark", poll_interval=0.5, max_workers=1)
        self.received_times = []
        self.message_event = threading.Event()

    def process_action(self, action: str, payload: dict):
        if action == "test":
            recv_time = time.time()
            send_time = payload.get("send_time")
            latency = recv_time - send_time
            self.received_times.append(latency)
            self.message_event.set()

def run_benchmark():
    print("🚀 Starting IPC Benchmark...")
    agent = BenchmarkAgent()

    # Start agent in a separate thread
    agent_thread = threading.Thread(target=agent.run, daemon=True)
    agent_thread.start()

    # Give it a moment to initialize
    time.sleep(1)

    latencies = []
    iterations = 10

    try:
        for i in range(iterations):
            agent.message_event.clear()
            send_time = time.time()

            # Send command
            send_command("benchmark", "test", {"send_time": send_time})

            # Wait for processing
            if agent.message_event.wait(timeout=2.0):
                latency = agent.received_times[-1]
                latencies.append(latency)
                print(f"  Iteration {i+1}: {latency*1000:.2f} ms")
            else:
                print(f"  Iteration {i+1}: TIMEOUT")

            # Wait a bit before next send to ensure we are testing the wait mechanism
            time.sleep(0.6)

    finally:
        agent.stop()
        agent_thread.join(timeout=1)

    if latencies:
        avg = statistics.mean(latencies)
        median = statistics.median(latencies)
        stdev = statistics.stdev(latencies) if len(latencies) > 1 else 0
        print("\n📊 Results:")
        print(f"  Average Latency: {avg*1000:.2f} ms")
        print(f"  Median Latency:  {median*1000:.2f} ms")
        print(f"  Std Dev:         {stdev*1000:.2f} ms")
    else:
        print("\n❌ No successful measurements.")

if __name__ == "__main__":
    run_benchmark()
