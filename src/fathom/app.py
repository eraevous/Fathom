"""Desktop launcher (spec 031): a small native window over the ordinary CLI.

The window chooses files (a browser can't hand a local path to the loopback server
without an upload or a path parameter, which spec 024 excludes), then runs the same
`guide` commands in-process and opens their saved pages. The browser half is the
unchanged `guide serve` session. tkinter is imported only when the window opens;
without it, `guide app` exits 2 with the fix and the equivalent commands (DG-RF).
"""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from io import StringIO
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import webbrowser

WORKSPACE_NAME = "Fathom"
# Folder names that usually mean a cloud-synced location. Reports can hold source
# values, so writing there may copy them off the machine; the window warns.
SYNCED_MARKERS = ("onedrive", "dropbox", "google drive", "googledrive", "icloud", "mobile documents", "cloudstorage", "box sync")

NO_TK = ("guide app: the desktop window needs tkinter, which this Python doesn't include.\n"
         "Fix: install a Python that ships it (python.org installers do; on Debian/Ubuntu: "
         "sudo apt install python3-tk; with Homebrew: brew install python-tk).\n"
         "Everything the window does is also a command:\n"
         "  guide liftoff DATA.csv --out DIR/liftoff\n"
         "  guide profile DATA.csv [--config fathom.yaml] --out DIR/profile\n"
         "  guide serve DATA.csv [--config fathom.yaml] --out DIR/working")


def workspace(home: Path | None = None) -> Path:
    return Path(home if home is not None else Path.home()) / WORKSPACE_NAME


def safe_name(stem: str) -> str:
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._") or "table"
    return name[:80]


def default_output(csv: Path | str, home: Path | None = None) -> Path:
    return workspace(home) / safe_name(Path(csv).stem)


# Whole folder names that mean a sync client's root (Box Drive's is plain "Box").
SYNCED_FOLDERS = ("box",)


def synced_location(path: Path | str) -> bool:
    text = str(path).lower()
    parts = re.split(r"[\\/]+", text)
    return any(marker in text for marker in SYNCED_MARKERS) or any(part in SYNCED_FOLDERS for part in parts)


@dataclass(frozen=True)
class Outcome:
    code: int
    messages: str
    page: Path | None

    @property
    def ok(self) -> bool:
        return self.code == 0 and self.page is not None and self.page.exists()


def run_cli(argv: list[str]) -> tuple[int, str]:
    """Run one `guide` command in this process and return its exit code and messages."""
    from .cli import main
    from .serve import PROFILE_LOCK
    buffer = StringIO()
    with PROFILE_LOCK, redirect_stdout(buffer), redirect_stderr(buffer):
        try:
            code = main(argv)
        except SystemExit as stop:  # argparse errors
            code = stop.code if isinstance(stop.code, int) else 2
    return int(code or 0), buffer.getvalue()


def quick_look(csv: Path, out: Path) -> Outcome:
    target = Path(out) / "liftoff"
    code, text = run_cli(["liftoff", str(csv), "--out", str(target)])
    return Outcome(code, text, target / "liftoff.html")


def profile(csv: Path, out: Path, config: Path | None = None) -> Outcome:
    target = Path(out) / "profile"
    argv = ["profile", str(csv), "--out", str(target)]
    if config:
        argv[2:2] = ["--config", str(config)]
    code, text = run_cli(argv)
    return Outcome(code, text, target / "report.html")


def recent_reports(home: Path | None = None, limit: int = 20) -> list[tuple[str, Path]]:
    """Saved pages under the workspace, newest first: (label, page path)."""
    root = workspace(home)
    if not root.is_dir():
        return []
    found = []
    for table in root.iterdir():
        if not table.is_dir() or table.is_symlink():
            continue
        for kind, page in (("profile", "report.html"), ("liftoff", "liftoff.html"), ("working", "report.html")):
            path = table / kind / page
            if path.is_file():
                found.append((path.stat().st_mtime, f"{table.name} · {kind}", path))
    found.sort(key=lambda item: (-item[0], item[1]))
    return [(label, path) for _, label, path in found[:limit]]


def open_page(path: Path) -> None:
    webbrowser.open(Path(path).resolve().as_uri())


def open_page_url(url: str) -> None:
    """Open the serve session's private loopback URL in the default browser."""
    if not url.startswith("http://127.0.0.1:"):
        raise ValueError("only the local session URL is opened")
    webbrowser.open(url)


def open_folder(path: Path) -> None:
    path = Path(path)
    if sys.platform.startswith("win"):
        os.startfile(path)  # noqa: S606 - the user's own folder
    else:
        subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(path)])


class ServeSession:
    """The unchanged `guide serve` session, driven from a background thread."""

    def __init__(self, csv: Path, out: Path, config: Path | None = None, *, idle_timeout: float = 1800):
        from .serve import create_server
        self.server = create_server(csv, Path(out) / "working", config, idle_timeout=idle_timeout)
        session = self.server.session
        self.url = session.origin + "/?token=" + session.token
        self.thread = threading.Thread(target=self._loop, name="fathom-serve", daemon=True)

    def _loop(self):
        from .serve import serve_until_stopped
        serve_until_stopped(self.server)

    def start(self) -> "ServeSession":
        self.thread.start()
        return self

    @property
    def running(self) -> bool:
        return self.thread.is_alive()

    def request_stop(self) -> None:
        """Ask the loop to stop; it finishes any rerun in progress first. Non-blocking."""
        self.server.session.stopped = True

    def stop(self, wait: float | None = None) -> None:
        """Stop and wait for the loop (and any rerun) to finish; `None` waits as long as it takes."""
        self.request_stop()
        if self.thread.is_alive():
            self.thread.join(wait)


def check() -> int:
    """Headless check for installers and CI: can the window open here?"""
    try:
        import tkinter  # noqa: F401
    except ImportError:
        print(NO_TK, file=sys.stderr)
        return 2
    print(f"guide app: tkinter {tkinter.TkVersion}; workspace {workspace()}")
    return 0


def main(*, check_only: bool = False, home: Path | None = None) -> int:
    if check_only:
        return check()
    try:
        import tkinter  # noqa: F401
    except ImportError:
        print(NO_TK, file=sys.stderr)
        return 2
    from .serve import install_network_guard
    install_network_guard()  # the window needs no network; loopback serve is still allowed
    from .app_window import LauncherWindow
    window = LauncherWindow(home=home)
    window.run()
    return 0


def gui_main() -> int:
    """Entry point for the `fathom-app` GUI script (no console window on Windows)."""
    for name in ("stdout", "stderr"):
        if getattr(sys, name) is None:  # pythonw has no console streams
            setattr(sys, name, StringIO())
    return main()  # the installer runs `guide app --check` first, so a missing tkinter is reported there
