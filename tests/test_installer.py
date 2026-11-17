"""Spec 031: the per-user installer's plan, launchers and uninstall (no network, no pip)."""
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("fathom_install", ROOT / "install" / "fathom_install.py")
inst = importlib.util.module_from_spec(SPEC)
sys.modules["fathom_install"] = inst  # dataclasses look up the module
SPEC.loader.exec_module(inst)


def test_system_names():
    assert [inst.system_name(p) for p in ("win32", "darwin", "linux")] == ["windows", "macos", "linux"]


def test_plans_stay_in_the_users_own_folders(tmp_path):
    home = tmp_path / "home"
    win = inst.make_plan("windows", home, {"LOCALAPPDATA": "C:/Users/a/AppData/Local", "APPDATA": "C:/Users/a/AppData/Roaming"})
    assert win.venv == Path("C:/Users/a/AppData/Local/Fathom/venv")
    assert win.app.name == "fathom-app.exe" and win.app.parent.name == "Scripts"
    assert win.launchers[0][1] == Path("C:/Users/a/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Fathom.lnk")
    mac = inst.make_plan("macos", home, {})
    assert mac.venv == home / "Library" / "Application Support" / "Fathom" / "venv"
    assert mac.launchers == [("app", home / "Applications" / "Fathom.app")]
    lin = inst.make_plan("linux", home, {"XDG_DATA_HOME": str(tmp_path / "xdg")})
    assert lin.venv == tmp_path / "xdg" / "fathom" / "venv"
    assert [p for _, p in lin.launchers] == [tmp_path / "xdg" / "applications" / "fathom.desktop", home / ".local" / "bin" / "fathom-app"]
    for plan in (mac, lin):
        assert all(str(p).startswith(str(tmp_path)) for _, p in plan.launchers)


def test_pip_arguments_online_and_offline(tmp_path):
    plan = inst.make_plan("linux", tmp_path, {}, here=ROOT / "install", extras=("stats",))
    assert plan.wheelhouse is None and plan.pip_args()[-1] == str(ROOT) + "[stats]"
    here = tmp_path / "bundle"
    (here / "wheelhouse").mkdir(parents=True)
    offline = inst.make_plan("linux", tmp_path, {}, here=here)
    args = offline.pip_args()
    assert args[-1] == "fathom-guide" and "--no-index" in args and str(here / "wheelhouse") in args
    with pytest.raises(SystemExit, match="no fathom_guide wheel"):
        inst.check_source(offline)


def test_bundle_python_mismatch_is_explained(tmp_path, monkeypatch):
    here = tmp_path / "bundle"
    (here / "wheelhouse").mkdir(parents=True)
    (here / "wheelhouse" / "bundle.json").write_text(json.dumps({"python": "3.0"}), encoding="utf-8")
    plan = inst.make_plan("linux", tmp_path, {}, here=here)
    assert inst.bundle_python(plan) == "3.0"
    monkeypatch.setattr(inst, "matching_python", lambda *a: None)
    with pytest.raises(SystemExit, match="built for Python 3.0"):
        inst.ensure_bundle_python(plan, [])
    (here / "wheelhouse" / "bundle.json").write_text(json.dumps({"python": "%d.%d" % sys.version_info[:2]}), encoding="utf-8")
    inst.ensure_bundle_python(plan, [])  # matching: nothing to do


def test_launcher_contents():
    app = PurePosixPath("/opt/x y/venv/bin/fathom-app")  # these launchers are written on macOS and Linux only
    entry = inst.desktop_entry(app)
    assert 'Exec="/opt/x y/venv/bin/fathom-app"' in entry and "Terminal=false" in entry
    assert "<key>CFBundleExecutable</key><string>Fathom</string>" in inst.mac_info_plist()
    assert inst.mac_launcher_script(app) == '#!/bin/sh\nexec \'/opt/x y/venv/bin/fathom-app\' "$@"\n'
    script = inst.windows_shortcut_script(Path("C:/Users/O'Neil/AppData/Local/Fathom/venv/Scripts/fathom-app.exe"),
                                          Path("C:/Start/Fathom.lnk"), Path("C:/Users/O'Neil"))
    assert "O''Neil" in script and "GetFolderPath('Desktop')" in script and "WScript.Shell" in script


def test_dry_run_changes_nothing(tmp_path):
    env = dict(os.environ, HOME=str(tmp_path), USERPROFILE=str(tmp_path), XDG_DATA_HOME=str(tmp_path / "xdg"),
               LOCALAPPDATA=str(tmp_path / "local"), APPDATA=str(tmp_path / "roaming"))
    done = subprocess.run([sys.executable, str(ROOT / "install" / "fathom_install.py"), "--dry-run"],
                          env=env, capture_output=True, text=True, check=True)
    assert "would run:" in done.stdout and "would add" in done.stdout
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("system", ["linux", "macos"])
def test_launchers_manifest_and_uninstall_round_trip(tmp_path, system):
    if system == "linux" and sys.platform.startswith("win"):
        pytest.skip("symlinks")
    home = tmp_path / "home"
    plan = inst.make_plan(system, home, {})
    plan.app.parent.mkdir(parents=True)
    plan.app.write_text("#!/bin/sh\n", encoding="utf-8")
    created = inst.add_launchers(plan)
    inst.write_manifest(plan, created)
    for _, path in plan.launchers:
        assert path.exists() or path.is_symlink()
    if system == "macos" and not sys.platform.startswith("win"):
        assert (plan.launchers[0][1] / "Contents" / "MacOS" / "Fathom").stat().st_mode & 0o111
    reports = home / "Fathom" / "t" / "profile"
    reports.mkdir(parents=True)
    (reports / "report.html").write_text("kept", encoding="utf-8")
    inst.uninstall(plan)
    assert not plan.venv.exists() and not plan.data.exists()
    assert not any(path.exists() or path.is_symlink() for _, path in plan.launchers)
    assert (reports / "report.html").read_text(encoding="utf-8") == "kept"


def test_unknown_extras_are_refused(capsys):
    with pytest.raises(SystemExit):
        inst.main(["--extras", "nope", "--dry-run"])
    assert "unknown extras" in capsys.readouterr().err


def test_windows_wrapper_has_crlf_and_no_admin_steps():
    bat = (ROOT / "install" / "Install Fathom.bat").read_bytes()
    assert b"\r\n" in bat and b"\n" not in bat.replace(b"\r\n", b"")
    text = bat.decode("ascii").lower()
    assert "runas" not in text and "setx" not in text and "reg add" not in text


def test_an_environment_from_another_python_is_rebuilt(tmp_path, monkeypatch):
    plan = inst.make_plan("linux", tmp_path, {})
    plan.python.parent.mkdir(parents=True)
    plan.python.write_text("", encoding="utf-8")
    (plan.venv / "stale").write_text("old", encoding="utf-8")
    calls = []
    monkeypatch.setattr(inst, "run", calls.append)
    monkeypatch.setattr(inst, "venv_python_version", lambda plan: "3.0")
    inst.make_venv(plan)
    assert not (plan.venv / "stale").exists() and calls and calls[0][1:3] == ["-m", "venv"]
    plan.python.parent.mkdir(parents=True)
    plan.python.write_text("", encoding="utf-8")
    calls.clear()
    monkeypatch.setattr(inst, "venv_python_version", lambda plan: "%d.%d" % sys.version_info[:2])
    inst.make_venv(plan)
    assert calls == []  # same Python: upgraded in place


def test_existing_launchers_the_installer_did_not_create_are_left_alone(tmp_path):
    if sys.platform.startswith("win"):
        pytest.skip("symlinks")
    home = tmp_path / "home"
    plan = inst.make_plan("linux", home, {})
    plan.app.parent.mkdir(parents=True)
    plan.app.write_text("#!/bin/sh\n", encoding="utf-8")
    entry, command = (path for _, path in plan.launchers)
    command.parent.mkdir(parents=True)
    command.write_text("the user's own script", encoding="utf-8")
    created = inst.add_launchers(plan)
    assert created == [str(entry)] and command.read_text(encoding="utf-8") == "the user's own script"
    inst.write_manifest(plan, created)
    inst.uninstall(plan)
    assert command.read_text(encoding="utf-8") == "the user's own script" and not entry.exists()


def test_mac_app_not_ours_is_not_modified_or_removed(tmp_path):
    home = tmp_path / "home"
    plan = inst.make_plan("macos", home, {})
    bundle = plan.launchers[0][1]
    (bundle / "Contents" / "Resources").mkdir(parents=True)
    (bundle / "Contents" / "Resources" / "keep").write_text("x", encoding="utf-8")
    assert inst.add_launchers(plan) == []
    inst.write_manifest(plan, [])
    inst.uninstall(plan)
    assert (bundle / "Contents" / "Resources" / "keep").exists() and not (bundle / "Contents" / "MacOS").exists()


def test_upgrades_keep_earlier_launcher_records(tmp_path):
    plan = inst.make_plan("windows", tmp_path, {"LOCALAPPDATA": str(tmp_path / "local"), "APPDATA": str(tmp_path / "roaming")})
    inst.write_manifest(plan, ["C:/Start/Fathom.lnk", "C:/Desk/Fathom.lnk"])
    inst.write_manifest(plan, [])  # an upgrade where PowerShell was blocked
    assert inst.read_manifest(plan) == ["C:/Start/Fathom.lnk", "C:/Desk/Fathom.lnk"]


def test_partial_shortcut_results_are_recorded():
    saved, skipped = inst.shortcut_results("SAVED:C:\\S\\Fathom.lnk\r\nSKIPPED:C:\\D\\Fathom.lnk\r\nnoise\r\n")
    assert saved == ["C:\\S\\Fathom.lnk"] and skipped == ["C:\\D\\Fathom.lnk"]
    script = inst.windows_shortcut_script(Path("C:/x/fathom-app.exe"), Path("C:/S/Fathom.lnk"), Path("C:/x"), ["C:/S/Fathom.lnk"])
    assert "Test-Path -LiteralPath" in script and "'SAVED:'" in script and "$owned=@('C:" in script


def test_awkward_paths_are_escaped_for_the_desktop_entry_and_the_shell(tmp_path):
    odd = PurePosixPath('/home/a$work/100%data/`x`/q"uote\\b/fathom-app')
    assert inst.desktop_exec_arg(odd) == '"/home/a\\\\$work/100%%data/\\\\`x\\\\`/q\\\\"uote\\\\\\\\b/fathom-app"'
    if sys.platform.startswith("win"):
        return
    target = tmp_path / "a$work `x` 'q'" / "fathom-app"
    target.parent.mkdir()
    target.write_text('#!/bin/sh\necho "ran:$*"\n', encoding="utf-8")
    target.chmod(0o755)
    script = tmp_path / "Fathom"
    script.write_text(inst.mac_launcher_script(target), encoding="utf-8")
    script.chmod(0o755)
    assert subprocess.run([str(script), "one"], capture_output=True, text=True, check=True).stdout == "ran:one\n"


def test_menu_entry_is_recorded_even_if_the_command_link_fails(tmp_path, monkeypatch):
    if sys.platform.startswith("win"):
        pytest.skip("symlinks")
    plan = inst.make_plan("linux", tmp_path / "home", {})
    plan.app.parent.mkdir(parents=True)
    plan.app.write_text("#!/bin/sh\n", encoding="utf-8")
    entry, command = (path for _, path in plan.launchers)

    def refuse(self, *a, **k):
        raise PermissionError("read-only")
    monkeypatch.setattr(Path, "symlink_to", refuse)
    created = inst.add_launchers(plan)
    assert created == [str(entry)] and inst.read_manifest(plan) == [str(entry)]
    inst.uninstall(plan)
    assert not entry.exists()
