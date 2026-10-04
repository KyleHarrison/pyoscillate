import logging
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from pyoscillate.cli import CrashLog, MasterRackCli


class CrashLogTests(unittest.TestCase):
    def setUp(self) -> None:
        # keep the exit hook from logging a fake crash when pytest exits
        patcher = patch("pyoscillate.cli.atexit.register")
        patcher.start()
        self.addCleanup(patcher.stop)
        root = logging.getLogger()
        self.addCleanup(setattr, root, "handlers", list(root.handlers))
        self.addCleanup(root.setLevel, root.level)
        self.addCleanup(setattr, sys, "excepthook", sys.excepthook)
        self.addCleanup(setattr, threading, "excepthook", threading.excepthook)
        self.addCleanup(setattr, sys, "unraisablehook", sys.unraisablehook)
        self.addCleanup(logging.captureWarnings, False)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.directory = Path(tmp.name) / "logs"

    def test_start_creates_the_log_file_and_records_the_run(self) -> None:
        log = CrashLog(self.directory, "demo", debug=False)
        path = log.start()
        logging.shutdown()
        self.assertEqual(path.parent, self.directory)
        self.assertIn("log file:", path.read_text())

    def test_uncaught_exception_is_written_with_its_traceback(self) -> None:
        log = CrashLog(self.directory, "demo", debug=False)
        path = log.start()
        try:
            raise ValueError("boom")
        except ValueError:
            log._handle_exception(*sys.exc_info())
        logging.shutdown()
        text = path.read_text()
        self.assertIn("uncaught exception", text)
        self.assertIn("ValueError: boom", text)

    def test_thread_exception_is_written(self) -> None:
        log = CrashLog(self.directory, "demo", debug=False)
        path = log.start()

        def fail() -> None:
            raise RuntimeError("audio thread died")

        thread = threading.Thread(target=fail, name="worker")
        thread.start()
        thread.join()
        logging.shutdown()
        text = path.read_text()
        self.assertIn("uncaught exception in thread worker", text)
        self.assertIn("audio thread died", text)

    def test_only_the_newest_runs_are_kept(self) -> None:
        self.directory.mkdir()
        for index in range(CrashLog.KEEP_RUNS + 5):
            (self.directory / f"demo-2000010{index:03d}.log").touch()
        CrashLog(self.directory, "demo", debug=False).start()
        logging.shutdown()
        self.assertEqual(
            len(list(self.directory.glob("demo-*.log"))), CrashLog.KEEP_RUNS
        )

    def test_debug_flag_lowers_the_log_level(self) -> None:
        CrashLog(self.directory, "demo", debug=True).start()
        self.assertEqual(logging.getLogger().level, logging.DEBUG)

    def test_cli_defaults_log_to_the_repo_logs_folder(self) -> None:
        args = MasterRackCli.parse([])
        self.assertEqual(args.log_dir, MasterRackCli.REPO_ROOT / "logs")
        self.assertFalse(args.debug)


if __name__ == "__main__":
    unittest.main()
