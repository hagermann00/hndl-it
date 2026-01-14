import json
import os
import uuid
from datetime import datetime
import time

DATA_FILE = os.path.join(os.path.dirname(__file__), 'todos_v2.json')

class TodoItInterface:
    """
    Headless interface for agents to interact with Todo-It.
    Operates directly on the JSON data.
    """
    
    def __init__(self, filepath=None):
        self.filepath = filepath or DATA_FILE
    
    def _read(self):
        if not os.path.exists(self.filepath):
            return {"version": "2.0", "items": []}
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading DB: {e}")
            return {"version": "2.0", "items": []}

    def _write(self, data):
        # Basic atomic write attempt
        temp_file = self.filepath + ".tmp"
        try:
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            os.replace(temp_file, self.filepath)
        except Exception as e:
            print(f"Error writing DB: {e}")

    def add_task(self, text, parent_id=None, agent_id="system"):
        """Adds a new task."""
        data = self._read()
        items = data.get("items", [])
        
        new_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
        new_task = {
            "id": new_id,
            "parent_id": parent_id,
            "text": text,
            "responsibility": {
                "agent_id": agent_id,
                "lock_status": "unlocked"
            },
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "payload": {
                "notes": "",
                "links": [],
                "tags": []
            }
        }
        
        items.append(new_task)
        data["items"] = items
        self._write(data)
        return new_id

    def get_tasks(self, parent_id=None, agent_id=None):
        """Get tasks, optionally filtered."""
        data = self._read()
        items = data.get("items", [])
        results = []
        for item in items:
            match = True
            if parent_id is not None and item.get('parent_id') != parent_id:
                match = False
            if agent_id is not None and item.get('responsibility', {}).get('agent_id') != agent_id:
                match = False
                
            if match:
                results.append(item)
        return results

    def claim_task(self, task_id, agent_id):
        """Assign responsibility to an agent."""
        data = self._read()
        items = data.get("items", [])
        found = False
        
        for item in items:
            if item['id'] == task_id:
                item['responsibility']['agent_id'] = agent_id
                item['responsibility']['lock_status'] = 'locked'
                found = True
                break
                
        if found:
            self._write(data)
            return True
        return False

    def complete_task(self, task_id):
        """Mark a task as completed."""
        data = self._read()
        items = data.get("items", [])
        found = False
        
        for item in items:
            if item['id'] == task_id:
                item['status'] = 'completed'
                found = True
                break
                
        if found:
            self._write(data)
            return True
        return False

# Quick Test
if __name__ == "__main__":
    api = TodoItInterface()
    print("Tasks:", len(api.get_tasks()))
    # id = api.add_task("Test from API")
    # print("Added:", id)
