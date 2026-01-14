"""
Evaluation Logger for hndl-it
Logs agent performance, errors, and LLM outputs for future optimization/evaluation.
"""
import os
import json
import time
from datetime import datetime
from pathlib import Path

# Config - Use D: drive for logs as per Storage Standard, fallback to C:
PRIMARY_LOG_DIR = Path(r"D:\hndl-it\logs\evals")
FALLBACK_LOG_DIR = Path(os.environ.get("APPDATA", "C:")) / "hndl-it" / "logs" / "evals"

class EvalLogger:
    def __init__(self, agent_name: str = "general"):
        self.agent_name = agent_name
        self.log_dir = self._get_valid_log_dir()
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"{self.agent_name}.jsonl"

    def _get_valid_log_dir(self) -> Path:
        """Check if D: is available, else fallback."""
        try:
            if PRIMARY_LOG_DIR.parent.parent.exists():
                return PRIMARY_LOG_DIR
        except:
            pass
        return FALLBACK_LOG_DIR

    def log(self, agent: str, task: str, output: str, error: str = None, meta: dict = None):
        """Standard log implementation."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "task": task,
            "output": output,
            "error": error,
            "success": error is None,
            "meta": meta or {}
        }
        self._write_entry(entry)

    def log_task(self, input_text: str, output_text: str, meta: dict = None, error: str = None):
        """Simplified task-centric logging for agents."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.agent_name,
            "input": input_text,
            "output": output_text,
            "error": error,
            "success": error is None,
            "meta": meta or {}
        }
        self._write_entry(entry)

    def _write_entry(self, entry: dict):
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"Failed to write log: {e}")

# Singleton support for backward compatibility
_instance = None

def get_eval_logger(agent_name: str = "general") -> EvalLogger:
    global _instance
    if _instance is None:
        _instance = EvalLogger(agent_name)
    return _instance

def log_eval(agent: str, task: str, output: str, error: str = None, meta: dict = None):
    get_eval_logger().log(agent, task, output, error, meta)

if __name__ == "__main__":
    # Test
    log_eval("test_agent", "Summarize this code", "The code is good.", meta={"runtime": 0.5})
    print(f"Log written to {EVAL_LOG_DIR}")
