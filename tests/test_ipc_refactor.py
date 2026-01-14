import unittest
import os
import json
import time
from shared import ipc

class TestIPC(unittest.TestCase):
    def setUp(self):
        self.test_target = "test_agent"
        # Ensure clean state
        ipc.clear_all()

    def tearDown(self):
        ipc.clear_all()

    def test_send_and_receive(self):
        payload = {"foo": "bar"}
        success = ipc.send_command(self.test_target, "test_action", payload)
        self.assertTrue(success)

        # Check file exists
        fpath = ipc.get_mailbox_path(self.test_target)
        self.assertTrue(os.path.exists(fpath))

        # Receive
        action, data = ipc.check_mailbox(self.test_target)
        self.assertEqual(action, "test_action")
        self.assertEqual(data["foo"], "bar")

        # File should be gone
        self.assertFalse(os.path.exists(fpath))

    def test_atomic_overwrite(self):
        # Write 1
        ipc.send_command(self.test_target, "action1", {"id": 1})
        # Write 2 immediately (simulating fast overwrite)
        ipc.send_command(self.test_target, "action2", {"id": 2})

        action, data = ipc.check_mailbox(self.test_target)
        # Should get the latest
        self.assertEqual(action, "action2")
        self.assertEqual(data["id"], 2)

if __name__ == '__main__':
    unittest.main()
