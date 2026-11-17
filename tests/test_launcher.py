"""Spec 031: the desktop launcher's logic, its CLI entry and a Tk smoke test."""
import builtins
import http.client
import os
from pathlib import Path
import time
from urllib.parse import urlsplit

import pytest

from fathom import app
from fathom.cli import main

FIXTURES = Path(__file__).parent / "fixtures"
CSV = FIXTURES / "review.csv"
YAML = FIXTURES / "review.yaml"


def test_default_output_is_a_safe_folder_under_the_workspace(tmp_path):
    assert app.workspace(tmp_path) == tmp_path / "Fathom"
    assert app.default_output("/data/Q3 sales (final).csv", tmp_path) == tmp_path / "Fathom" / "Q3_sales_final"
    assert app.default_output("../..csv", tmp_path).name == "table"
    assert app.default_output(CSV, tmp_path).parent == tmp_path / "Fathom"


@pytest.mark.parametrize("path, synced", [
    ("C:/Users/a/OneDrive - Org/Desktop/x", True), ("/Users/a/Library/Mobile Documents/x", True),
    ("/Users/a/Library/CloudStorage/GoogleDrive-a/x", True), ("/home/a/Dropbox/x", True),
    ("/home/a/Fathom/x", False), ("C:/Users/a/Fathom/x", False)])
def test_synced_locations_are_flagged(path, synced):
    assert app.synced_location(path) is synced


def test_launcher_actions_write_the_same_bytes_as_the_cli(tmp_path):
    out = app.default_output(CSV, tmp_path)
    look = app.quick_look(CSV, out)
    prof = app.profile(CSV, out, YAML)
    assert look.ok and prof.ok and "guide: wrote" in look.messages
    assert main(["liftoff", str(CSV), "--out", str(tmp_path / "cli-liftoff")]) == 0
    assert main(["profile", str(CSV), "--config", str(YAML), "--out", str(tmp_path / "cli-profile")]) == 0
    for name in ("liftoff.html", "liftoff-profile.json"):
        assert (out / "liftoff" / name).read_bytes() == (tmp_path / "cli-liftoff" / name).read_bytes()
    for name in ("report.html", "report.md", "guide-profile.json"):
        assert (out / "profile" / name).read_bytes() == (tmp_path / "cli-profile" / name).read_bytes()


def test_failures_are_reported_not_raised(tmp_path):
    missing = app.profile(tmp_path / "absent.csv", tmp_path / "out")
    assert missing.code != 0 and not missing.ok
    bad = tmp_path / "bad.yaml"
    bad.write_text("schema: [", encoding="utf-8")
    assert not app.profile(CSV, tmp_path / "out2", bad).ok


def test_recent_reports_are_newest_first_and_ignore_other_files(tmp_path):
    root = app.workspace(tmp_path)
    assert app.recent_reports(tmp_path) == []
    old = root / "old" / "profile"
    new = root / "new" / "liftoff"
    for folder, page in ((old, "report.html"), (new, "liftoff.html")):
        folder.mkdir(parents=True)
        (folder / page).write_text("<html></html>", encoding="utf-8")
    (root / "stray.txt").write_text("x", encoding="utf-8")
    (root / "empty").mkdir()
    os.utime(old / "report.html", (1, 1))
    labels = [label for label, _ in app.recent_reports(tmp_path)]
    assert labels == ["new · liftoff", "old · profile"]


def test_serve_session_runs_in_a_thread_and_stops(tmp_path):
    session = app.ServeSession(CSV, tmp_path / "t", idle_timeout=60).start()
    try:
        assert session.running and session.url.startswith("http://127.0.0.1:")
        parts = urlsplit(session.url)
        conn = http.client.HTTPConnection(parts.hostname, parts.port, timeout=5)
        conn.request("GET", "/?" + parts.query, headers={"Host": parts.netloc})
        assert conn.getresponse().status == 200
        conn.close()
    finally:
        session.stop()
    assert not session.running
    assert (tmp_path / "t" / "working" / "report.html").is_file()
    assert (tmp_path / "t" / "working" / "serve.log").read_text(encoding="utf-8").strip().endswith("session closed")


def test_only_the_local_session_url_is_opened():
    with pytest.raises(ValueError):
        app.open_page_url("https://example.com/")


def test_app_check_and_missing_tkinter_degrades(monkeypatch, capsys):
    real_import = builtins.__import__

    def no_tk(name, *args, **kwargs):
        if name == "tkinter" or name.startswith("tkinter."):
            raise ImportError("no tkinter")
        return real_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", no_tk)
    assert main(["app", "--check"]) == 2
    assert main(["app"]) == 2
    err = capsys.readouterr().err
    assert "needs tkinter" in err and "guide profile DATA.csv" in err


def _tk_root():
    tk = pytest.importorskip("tkinter")
    try:
        return tk.Tk()
    except tk.TclError:
        pytest.skip("no display")


def test_window_profiles_a_csv_and_opens_the_report(tmp_path, monkeypatch):
    root = _tk_root()
    from fathom import app_window
    opened = []
    monkeypatch.setattr(app, "open_page", opened.append)
    monkeypatch.setattr(app_window.messagebox, "showerror", lambda *a: pytest.fail(str(a)))
    window = app_window.LauncherWindow(home=tmp_path, root=root)
    try:
        window.csv.set(str(CSV))
        window.profile()
        deadline = time.monotonic() + 60
        while not opened and time.monotonic() < deadline:
            root.update()
            time.sleep(0.05)
        assert opened == [app.default_output(CSV, tmp_path) / "profile" / "report.html"]
        assert window.recent_paths[0] == opened[0]
        assert "Done." in window.status.get()
    finally:
        window.close()


def test_window_starts_and_stops_the_browser_session(tmp_path, monkeypatch):
    root = _tk_root()
    from fathom import app_window
    urls = []
    monkeypatch.setattr(app, "open_page_url", urls.append)
    monkeypatch.setattr(app_window.messagebox, "showerror", lambda *a: pytest.fail(str(a)))
    window = app_window.LauncherWindow(home=tmp_path, root=root)
    try:
        window.csv.set(str(CSV))
        window.start_serve()
        deadline = time.monotonic() + 60
        while not urls and time.monotonic() < deadline:
            root.update()
            time.sleep(0.05)
        assert urls and urls[0].startswith("http://127.0.0.1:")
        session = window.session
        assert session is not None and session.running
        window.stop_serve()
        assert window.session is None and not session.running
    finally:
        window.close()
