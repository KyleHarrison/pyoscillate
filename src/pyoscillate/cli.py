"""Command-line launchers for the Flet apps, with crash logging.

`MasterRackCli.main` is the `master-rack` console script. Every run writes a
timestamped log under `<repo>/logs/`, capturing Python log records, uncaught
exceptions on any thread or asyncio task, and native crashes (a segfault in
Pyo or PortAudio) through `faulthandler`. A run that ends without the
"clean shutdown" line crashed hard.

This is dev tooling for a source checkout: the Flet apps live in the repo's
`src/flet/` and are imported as `src.flet...`, so the repo root is put on
`sys.path` before the app is imported.
"""

from __future__ import annotations

import argparse
import atexit
import faulthandler
import importlib.metadata
import logging
import os
import platform
import sys
import threading
import traceback
import warnings
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from types import TracebackType
from typing import ClassVar, TextIO


class CrashLog:
    """Routes logs and every kind of crash for one run into a single file."""

    LOG_FORMAT: ClassVar[str] = (
        "%(asctime)s.%(msecs)03d %(levelname)-8s %(threadName)s %(name)s: %(message)s"
    )
    DATE_FORMAT: ClassVar[str] = "%Y-%m-%d %H:%M:%S"
    # older logs beyond this many are deleted when a new one is created
    KEEP_RUNS: ClassVar[int] = 20

    def __init__(self, directory: Path, name: str, debug: bool) -> None:
        self.directory = directory
        self.name = name
        self.debug = debug
        self.path = (
            directory / f"{name}-{datetime.now().astimezone():%Y%m%d-%H%M%S}.log"
        )
        self.logger = logging.getLogger("pyoscillate")
        self._stream: TextIO | None = None
        self._clean = False

    def start(self) -> Path:
        """Open the log file, install every crash hook and return the file's path."""
        self.directory.mkdir(parents=True, exist_ok=True)
        self._prune()
        level = logging.DEBUG if self.debug else logging.INFO

        file_handler = logging.FileHandler(self.path, encoding="utf-8")
        console = logging.StreamHandler()
        root = logging.getLogger()
        root.setLevel(level)
        for handler in (file_handler, console):
            handler.setFormatter(logging.Formatter(self.LOG_FORMAT, self.DATE_FORMAT))
            root.addHandler(handler)
        # the file's own descriptor, so a native crash lands in the same file
        self._stream = file_handler.stream

        faulthandler.enable(file=self._stream, all_threads=True)
        sys.excepthook = self._handle_exception
        threading.excepthook = self._handle_thread_exception
        sys.unraisablehook = self._handle_unraisable
        logging.captureWarnings(True)
        if self.debug:
            warnings.simplefilter("default")
        atexit.register(self._finish)

        self.logger.info("log file: %s", self.path)
        self.logger.info("command: %s", " ".join(sys.argv))
        self.logger.info(
            "python %s on %s, debug=%s",
            platform.python_version(),
            platform.platform(),
            self.debug,
        )
        self._log_versions()
        return self.path

    def mark_clean(self) -> None:
        self._clean = True

    def _log_versions(self) -> None:
        for package in ("flet", "pyo"):
            try:
                version = importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:
                version = "not installed"
            self.logger.info("%s %s", package, version)

    def _prune(self) -> None:
        old = sorted(self.directory.glob(f"{self.name}-*.log"))
        for path in old[: max(0, len(old) - self.KEEP_RUNS + 1)]:
            path.unlink(missing_ok=True)

    def _finish(self) -> None:
        if self._clean:
            self.logger.info("clean shutdown")
        else:
            self.logger.error("process exiting without a clean shutdown")
        logging.shutdown()

    def _handle_exception(
        self,
        exc_type: type[BaseException],
        exc: BaseException,
        tb: TracebackType | None,
    ) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            self.logger.info("interrupted by user")
            self._clean = True
            return
        self.logger.critical("uncaught exception", exc_info=(exc_type, exc, tb))

    def _handle_thread_exception(self, args: threading.ExceptHookArgs) -> None:
        if args.exc_type is SystemExit or args.exc_value is None:
            return
        name = args.thread.name if args.thread else "unknown"
        self.logger.critical(
            "uncaught exception in thread %s",
            name,
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )

    def _handle_unraisable(self, args: sys.UnraisableHookArgs) -> None:
        self.logger.error(
            "unraisable exception in %r: %s\n%s",
            args.object,
            args.err_msg,
            "".join(
                traceback.format_exception(
                    args.exc_type, args.exc_value, args.exc_traceback
                )
            ),
        )


class MasterRackCli:
    """The `master-rack` console script."""

    NAME: ClassVar[str] = "master-rack"
    REPO_ROOT: ClassVar[Path] = Path(__file__).resolve().parents[2]
    LOG_DIR: ClassVar[Path] = REPO_ROOT / "logs"

    @classmethod
    def parse(cls, argv: Sequence[str] | None) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            prog=cls.NAME,
            description="Run the Master Rack Flet app, logging crashes to a file.",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="verbose DEBUG logging (including Flet's own), asyncio debug mode and all warnings",
        )
        parser.add_argument(
            "--log-dir",
            type=Path,
            default=cls.LOG_DIR,
            help="directory for the per-run log files (default: %(default)s)",
        )
        return parser.parse_args(argv)

    @classmethod
    def main(cls, argv: Sequence[str] | None = None) -> None:
        args = cls.parse(argv)
        crash_log = CrashLog(args.log_dir, cls.NAME, args.debug)
        crash_log.start()
        logger = crash_log.logger
        # the Flet apps import as `src.flet...`, which needs the repo root
        sys.path.insert(0, str(cls.REPO_ROOT))
        try:
            import flet as ft
            from src.flet.master_rack.app import main as app_main

            logger.info("starting Master Rack")
            if args.debug:
                # read when each event loop is created, so it covers Flet's
                os.environ["PYTHONASYNCIODEBUG"] = "1"
            ft.run(app_main)
        except KeyboardInterrupt:
            logger.info("interrupted by user")
        except SystemExit as exit_request:
            if exit_request.code not in (None, 0):
                logger.error("exiting with status %r", exit_request.code)
                raise
        except BaseException:
            logger.critical("Master Rack crashed", exc_info=True)
            print(f"\nCrashed - see {crash_log.path}", file=sys.stderr)
            raise SystemExit(1) from None
        crash_log.mark_clean()
