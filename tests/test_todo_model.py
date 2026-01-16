import unittest
import sys
import os
import shutil
from unittest.mock import MagicMock

# --- Mocking PyQt6 ---
# We need to set this up before importing todo_model

# Mock classes
class MockQModelIndex:
    def __init__(self, row=0, column=0, ptr=None):
        self._row = row
        self._column = column
        self._ptr = ptr

    def isValid(self):
        return self._ptr is not None

    def internalPointer(self):
        return self._ptr

    def row(self):
        return self._row

    def column(self):
        return self._column

class MockQAbstractItemModel:
    def __init__(self, parent=None):
        pass

    def beginInsertRows(self, parent, first, last):
        pass

    def endInsertRows(self):
        pass

    def beginRemoveRows(self, parent, first, last):
        pass

    def endRemoveRows(self):
        pass

    def hasIndex(self, row, column, parent):
        return True

    def createIndex(self, row, column, ptr):
        return MockQModelIndex(row, column, ptr)

# Setup sys.modules
if 'PyQt6' not in sys.modules:
    qt_core = MagicMock()
    qt_core.QAbstractItemModel = MockQAbstractItemModel
    qt_core.QModelIndex = MockQModelIndex
    qt_core.Qt = MagicMock()
    qt_core.Qt.ItemDataRole = MagicMock()
    qt_core.Qt.ItemDataRole.DisplayRole = 1
    qt_core.pyqtSignal = MagicMock()

    sys.modules['PyQt6'] = MagicMock()
    sys.modules['PyQt6.QtCore'] = qt_core

# --- Import TodoModel ---
# Ensure todo-it is in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
todo_it_path = os.path.join(project_root, 'todo-it')
if todo_it_path not in sys.path:
    sys.path.append(todo_it_path)

from todo_model import TodoModel

class TestTodoModel(unittest.TestCase):
    def setUp(self):
        self.test_file = 'test_todos_unittest.json'
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        self.model = TodoModel(self.test_file)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_recursive_deletion(self):
        """Test that deleting a parent removes all children from all_nodes."""
        # 1. Add Parent
        parent_node = self.model.add_item("Parent")
        parent_id = parent_node.data['id']

        # 2. Add Child
        # Manually create parent index as we are mocking
        parent_index = MockQModelIndex(0, 0, parent_node)
        child_node = self.model.add_item("Child", parent_index)
        child_id = child_node.data['id']

        # 3. Add Grandchild to test deep recursion
        child_index = MockQModelIndex(0, 0, child_node)
        grandchild_node = self.model.add_item("Grandchild", child_index)
        grandchild_id = grandchild_node.data['id']

        # Verify all nodes present
        self.assertIn(parent_id, self.model.all_nodes)
        self.assertIn(child_id, self.model.all_nodes)
        self.assertIn(grandchild_id, self.model.all_nodes)

        # 4. Delete Parent
        self.model.delete_item(parent_index)

        # 5. Verify Cleanup
        self.assertNotIn(parent_id, self.model.all_nodes, "Parent should be removed")
        self.assertNotIn(child_id, self.model.all_nodes, "Child should be removed")
        self.assertNotIn(grandchild_id, self.model.all_nodes, "Grandchild should be removed")

if __name__ == '__main__':
    unittest.main()
