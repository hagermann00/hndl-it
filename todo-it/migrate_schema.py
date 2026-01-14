import json
import os
import uuid
from datetime import datetime

OLD_FILE = r'C:\IIWII_DB\hndl-it\todo-it\todos.json'
NEW_FILE = r'C:\IIWII_DB\hndl-it\todo-it\todos_v2.json'

def migrate_recursive(items, parent_id=None, flat_list=None):
    if flat_list is None:
        flat_list = []
        
    for item in items:
        # Keep existing ID if possible, else generate (though existing seems to have IDs)
        item_id = item.get('id', str(uuid.uuid4()))
        
        # Construct new flat item
        new_item = {
            "id": item_id,
            "parent_id": parent_id,
            "text": item.get('text', ''),
            "responsibility": {
                "agent_id": "user", # Default to user
                "lock_status": "unlocked"
            },
            "status": "completed" if item.get('completed') else "pending",
            "created_at": item.get('created_at', datetime.now().isoformat()),
            "payload": {
                "notes": item.get('notes', ''),
                "links": item.get('links', []),
                "tags": item.get('tags', [])
            }
        }
        
        # Handle highlight as a tag or separate field?
        # New model might handle highlight differently, but let's keep it if needed.
        if item.get('highlighted'):
            new_item['payload']['highlighted'] = True
            
        flat_list.append(new_item)
        
        # SQL-style recursion
        children = item.get('children', [])
        if children:
            migrate_recursive(children, item_id, flat_list)
            
    return flat_list

def main():
    if not os.path.exists(OLD_FILE):
        print(f"File not found: {OLD_FILE}")
        return

    with open(OLD_FILE, 'r') as f:
        old_data = json.load(f)

    flat_items = migrate_recursive(old_data)
    
    new_schema = {
        "version": "2.0",
        "items": flat_items
    }
    
    with open(NEW_FILE, 'w') as f:
        json.dump(new_schema, f, indent=2)
        
    print(f"Migration complete. Converted {len(flat_items)} items to {NEW_FILE}")

if __name__ == "__main__":
    main()
