import json
import os
import logging
from typing import Dict, Any, List

logger = logging.getLogger("hndl-it.floater.config")

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "settings.json")

DEFAULT_CONFIG = {
    "ollama_url": "http://localhost:11434",
    "active_model": "",
    "saved_tasks": [] 
    # Task Schema: {"id": str, "name": str, "commands": List[str]}
}

class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.config = DEFAULT_CONFIG.copy()
            cls._instance.load()
        return cls._instance

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    # Merge with default to ensure new keys exist
                    for key, val in DEFAULT_CONFIG.items():
                        if key not in data:
                            data[key] = val
                    self.config = data
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
        else:
            self.save() # Create default

    def save(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def get(self, key: str, default=None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        self.config[key] = value
        self.save()

    # Specialized Helpers for Memory/Tasks
    def get_tasks(self) -> List[Dict]:
        return self.config.get("saved_tasks", [])

    def add_task(self, name: str, commands: List[str]):
        import uuid
        task = {
            "id": str(uuid.uuid4()),
            "name": name,
            "commands": commands
        }
        tasks = self.get_tasks()
        tasks.append(task)
        self.set("saved_tasks", tasks)

    def remove_task(self, task_id: str):
        tasks = self.get_tasks()
        tasks = [t for t in tasks if t["id"] != task_id]
        self.set("saved_tasks", tasks)
