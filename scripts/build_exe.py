"""Package one Flet app as a standalone executable: `uv run python scripts/build_exe.py lofi`.

Runs the same on macOS and Windows, so a packaging problem can be reproduced
locally. The entry script is generated outside the package tree: PyInstaller
adds the first directory above a script's `__init__.py` chain to the module
path, and for `src/flet/<app>/app.py` that is `src/`, which makes `import flet`
resolve to this repo's `src/flet` instead of the Flet library.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ENTRY = """\
import flet as ft
from src.flet.{app}.app import main

ft.run(main)
"""


def main() -> None:
    app = sys.argv[1]
    app_dir = ROOT / "src" / "flet" / app
    if not (app_dir / "app.py").is_file():
        sys.exit(f"No app at {app_dir / 'app.py'}")

    with tempfile.TemporaryDirectory() as tmp:
        entry = Path(tmp) / f"{app}_entry.py"
        entry.write_text(ENTRY.format(app=app))
        cmd = [
            "flet", "pack", str(entry),
            "--name", app,
            "--distpath", str(ROOT / "dist"),
            f"--pyinstaller-build-args=--paths={ROOT}",
            "--pyinstaller-build-args=--collect-all=pyo",
            # the master rack finds patches with pkgutil at runtime, which
            # PyInstaller's static import analysis can't see
            "--pyinstaller-build-args=--collect-submodules=pyoscillate.patches",
            "--yes",
        ]  # fmt: skip
        presets = app_dir / "presets"
        if presets.is_dir():
            sep = ";" if sys.platform == "win32" else ":"
            cmd += ["--add-data", f"{presets}{sep}src/flet/{app}/presets"]
        subprocess.run(cmd, check=True, cwd=tmp)


if __name__ == "__main__":
    main()
