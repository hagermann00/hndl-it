import unittest
import os
import tempfile
import shutil
import time
from unittest.mock import patch, MagicMock
from agents.systems_engineer.monitor import SystemsEngineer
import agents.systems_engineer.monitor as monitor

class TestMonitorOptimization(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.agent = SystemsEngineer()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def create_log_file(self, filename, content):
        path = os.path.join(self.temp_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_scan_logs_finds_errors(self):
        # We temporarily override LOG_DIR in the module
        original_log_dir = monitor.LOG_DIR
        monitor.LOG_DIR = self.temp_dir

        try:
            # Create a log file with errors
            self.create_log_file("test_error.log", "INFO: Normal log\nERROR: Something went wrong\nCRITICAL: System failure\n")

            # Create a log file without errors
            self.create_log_file("test_clean.log", "INFO: All good\nINFO: Still good\n")

            # Override listdir is not needed if we point LOG_DIR to temp_dir and listdir is used on LOG_DIR
            # But the code uses os.listdir(LOG_DIR).
            # So if monitor.LOG_DIR is self.temp_dir, os.listdir(monitor.LOG_DIR) works.

            # However, we need to ensure mtime check passes.
            # The files are just created, so mtime is now.
            # CHECK_INTERVAL_SECONDS is 60. So they are fresh.

            issues = self.agent._scan_logs()

            # We expect 2 issues (ERROR and CRITICAL) from test_error.log
            self.assertEqual(len(issues), 2)
            self.assertTrue(any("ERROR: Something went wrong" in i for i in issues))
            self.assertTrue(any("CRITICAL: System failure" in i for i in issues))

            # Verify clean log produced no issues
            self.assertFalse(any("test_clean.log" in i for i in issues))

        finally:
            monitor.LOG_DIR = original_log_dir

    def test_read_last_n_lines(self):
        log_file = os.path.join(self.temp_dir, "test.log")

        # 1. Small file
        content = "Line 1\nLine 2\nLine 3\n"
        with open(log_file, "w") as f: f.write(content)
        lines = self.agent._read_last_n_lines(log_file, 2)
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "Line 2\n")
        self.assertEqual(lines[1], "Line 3\n")

        # 2. Large file (simulate by creating enough lines to force block reading)
        # 4096 bytes block size. Let's make 5000 bytes.
        long_line = "A" * 100 + "\n" # 101 bytes
        content = long_line * 50
        with open(log_file, "w") as f: f.write(content)

        lines = self.agent._read_last_n_lines(log_file, 10)
        self.assertEqual(len(lines), 10)
        self.assertEqual(lines[0], long_line)

        # 3. Exact lines
        with open(log_file, "w") as f: f.write("A\nB\nC\n")
        lines = self.agent._read_last_n_lines(log_file, 3)
        self.assertEqual(lines, ["A\n", "B\n", "C\n"])

        # 4. Empty file
        with open(log_file, "w") as f: f.write("")
        lines = self.agent._read_last_n_lines(log_file, 5)
        self.assertEqual(lines, [])

        # 5. File larger than block but fewer lines
        # 5000 bytes but only 1 line
        super_long = "B" * 5000 + "\n"
        with open(log_file, "w") as f: f.write(super_long)
        lines = self.agent._read_last_n_lines(log_file, 5)
        self.assertEqual(len(lines), 1)
        self.assertEqual(len(lines[0]), 5001)

if __name__ == "__main__":
    unittest.main()
