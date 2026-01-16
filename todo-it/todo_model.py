import json
import os
import uuid
from datetime import datetime
from PyQt6.QtCore import QAbstractItemModel, Qt, QModelIndex, pyqtSignal

class TodoNode:
    """Internal node for tree structure."""
    def __init__(self, data, parent=None):
        self.data = data
        self.parent = parent
        self.children = []
        
    def append_child(self, child):
        child.parent = self
        self.children.append(child)
    
    def child(self, row):
        if 0 <= row < len(self.children):
            return self.children[row]
        return None
    
    def row(self):
        if self.parent:
            return self.parent.children.index(self)
        return 0

class TodoModel(QAbstractItemModel):
    """
    QAbstractItemModel for flat relational todo items.
    Reconstructs the tree structure from the flat list on load.
    """
    dataChanged = pyqtSignal(QModelIndex, QModelIndex, list)
    
    def __init__(self, filename, parent=None):
        super().__init__(parent)
        self.filename = filename
        self.root_node = TodoNode({"text": "Root", "id": "root"})
        self.all_nodes = {} # Map ID -> Node
        self.load_data()

    def load_data(self):
        """Loads data from JSON and builds the tree."""
        if not os.path.exists(self.filename):
            self.save_data() # Create empty file if not exists
            return

        try:
            with open(self.filename, 'r') as f:
                content = json.load(f)
                
            items = content.get('items', [])
            
            # 1. Create all nodes
            self.all_nodes = {}
            temp_nodes = []
            for item in items:
                node = TodoNode(item)
                self.all_nodes[item['id']] = node
                temp_nodes.append(node)
                
            # 2. Build Hierarchy
            self.root_node.children = [] 
            for node in temp_nodes:
                parent_id = node.data.get('parent_id')
                if parent_id and parent_id in self.all_nodes:
                    parent_node = self.all_nodes[parent_id]
                    parent_node.append_child(node)
                else:
                    # No parent or parent not found -> Top Level
                    self.root_node.append_child(node)
                    
        except Exception as e:
            print(f"Error loading todo model: {e}")

    def save_data(self):
        """Flattens the tree and saves to JSON."""
        flat_items = []
        
        # Traverse tree to collect items
        stack = list(self.root_node.children)
        while stack:
            node = stack.pop(0) # BFS or DFS doesn't strictly matter for storage
            flat_items.append(node.data)
            stack.extend(node.children)
            
        output = {
            "version": "2.0",
            "items": flat_items
        }
        
        try:
            with open(self.filename, 'w') as f:
                json.dump(output, f, indent=2)
        except Exception as e:
            print(f"Error saving todo model: {e}")

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parent_node = self.root_node
        else:
            parent_node = parent.internalPointer()

        child_item = parent_node.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        
        return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        child_node = index.internalPointer()
        parent_node = child_node.parent

        if parent_node == self.root_node:
            return QModelIndex()

        return self.createIndex(parent_node.row(), 0, parent_node)

    def rowCount(self, parent=QModelIndex()):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parent_node = self.root_node
        else:
            parent_node = parent.internalPointer()

        return len(parent_node.children)

    def columnCount(self, parent=QModelIndex()):
        return 1

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        node = index.internalPointer()
        item_data = node.data

        if role == Qt.ItemDataRole.DisplayRole:
            prefix = "✓ " if item_data.get('status') == 'completed' else "○ "
            return prefix + item_data.get('text', '')
            
        elif role == Qt.ItemDataRole.UserRole:
            return item_data['id']
            
        elif role == Qt.ItemDataRole.ForegroundRole:
            # Basic styling hook - updated by View/Delegate later
            if item_data.get('status') == 'completed':
                return None # View handles this via delegate usually, or return QColor
            
        return None

    def add_item(self, text, parent_index=QModelIndex()):
        """Adds a new item to the model."""
        parent_node = self.root_node
        if parent_index.isValid():
            parent_node = parent_index.internalPointer()
            
        new_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
        
        new_data = {
            "id": new_id,
            "parent_id": parent_node.data['id'] if parent_node != self.root_node else None,
            "text": text,
            "responsibility": {"agent_id": "user", "lock_status": "unlocked"},
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "payload": {"notes": "", "links": [], "tags": []}
        }
        
        position = len(parent_node.children)
        self.beginInsertRows(parent_index, position, position)
        
        new_node = TodoNode(new_data, parent_node)
        parent_node.children.append(new_node)
        self.all_nodes[new_id] = new_node
        
        self.endInsertRows()
        self.save_data()
        return new_node
    
    def toggle_completion(self, index):
        if not index.isValid():
            return
            
        node = index.internalPointer()
        current = node.data.get('status', 'pending')
        new_status = 'completed' if current == 'pending' else 'pending'
        node.data['status'] = new_status
        
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
        self.save_data()
        
    def delete_item(self, index):
        if not index.isValid():
            return
            
        node = index.internalPointer()
        parent_node = node.parent
        row = node.row()
        
        # Determine parent index
        parent_index = self.parent(index)
        
        self.beginRemoveRows(parent_index, row, row)
        parent_node.children.pop(row)

        self._cleanup_node_recursive(node)

        self.endRemoveRows()
        self.save_data()

    def _cleanup_node_recursive(self, node):
        """Recursively removes a node and its children from all_nodes."""
        for child in node.children:
            self._cleanup_node_recursive(child)

        node_id = node.data.get('id')
        if node_id and node_id in self.all_nodes:
            del self.all_nodes[node_id]
