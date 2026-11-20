#!/usr/bin/env python3
"""Per-user Fathom installer (spec 031). Standard library only; no admin rights.

  python fathom_install.py              install or upgrade
  python fathom_install.py --dry-run    print the plan, change nothing
  python fathom_install.py --uninstall  remove exactly what an install created
  python fathom_install.py --extras stats,exports

Creates a private virtual environment in the user's data folder, installs Fathom
into it (offline from a `wheelhouse/` folder beside this script when present,
otherwise from the repository checkout this script sits in), and adds a launcher
for the desktop window. Touches nothing outside the user's own folders: no PATH,
registry or shell-profile changes. The user's reports in ~/Fathom are never removed.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

MIN_PYTHON = (3, 11)
HERE = Path(__file__).resolve().parent
MANIFEST = "install-manifest.json"
EXTRAS = ("stats", "pdf", "pptx", "exports")


def system_name(platform: str | None = None) -> str:
    platform = platform or sys.platform
    if platform.startswith("win"):
        return "windows"
    return "macos" if platform == "darwin" else "linux"


def data_dir(system: str, home: Path, env: dict) -> Path:
    if system == "windows":
        return Path(env.get("LOCALAPPDATA") or home / "AppData" / "Local") / "Fathom"
    if system == "macos":
        return home / "Library" / "Application Support" / "Fathom"
    return Path(env.get("XDG_DATA_HOME") or home / ".local" / "share") / "fathom"


def venv_bin(system: str, venv: Path) -> Path:
    return venv / ("Scripts" if system == "windows" else "bin")


@dataclass
class Plan:
    system: str
    home: Path
    data: Path
    venv: Path
    python: Path
    app: Path
    guide: Path
    source: str
    wheelhouse: Path | None
    extras: tuple[str, ...]
    launchers: list[tuple[str, Path]] = field(default_factory=list)

    @property
    def requirement(self) -> str:
        suffix = "[" + ",".join(self.extras) + "]" if self.extras else ""
        return ("fathom-guide" if self.wheelhouse else self.source) + suffix

    def pip_args(self) -> list[str]:
        args = [str(self.python), "-m", "pip", "--disable-pip-version-check", "install", "--upgrade"]
        if self.wheelhouse:
            args += ["--no-index", "--find-links", str(self.wheelhouse)]
        return args + [self.requirement]

    def reinstall_args(self) -> list[str] | None:
        """Offline only: reinstall the bundle's own Fathom wheel by path. `--upgrade` keeps an
        installed copy with the same version (0.1.0 for every build so far), so a rebuilt bundle
        would otherwise leave the old code in place (Codex review, #56). Dependencies were
        resolved by `pip_args`; `--no-deps` leaves them alone."""
        if not self.wheelhouse:
            return None
        wheels = sorted(self.wheelhouse.glob("fathom_guide-*.whl"))
        if not wheels:
            return None
        return [str(self.python), "-m", "pip", "--disable-pip-version-check", "install",
                "--force-reinstall", "--no-deps", "--no-index", str(wheels[-1])]


def make_plan(system: str, home: Path, env: dict, here: Path = HERE, extras: tuple[str, ...] = ()) -> Plan:
    data = data_dir(system, home, env)
    venv = data / "venv"
    scripts = venv_bin(system, venv)
    exe = ".exe" if system == "windows" else ""
    wheelhouse = here / "wheelhouse"
    plan = Plan(system, home, data, venv, scripts / ("python" + exe), scripts / ("fathom-app" + exe),
                scripts / ("guide" + exe), str(here.parent), wheelhouse if wheelhouse.is_dir() else None, extras)
    if system == "windows":
        programs = Path(env.get("APPDATA") or home / "AppData" / "Roaming") / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        plan.launchers = [("start-menu shortcut", programs / "Fathom.lnk"), ("desktop shortcut", Path("<Desktop>") / "Fathom.lnk")]
    elif system == "macos":
        plan.launchers = [("app", home / "Applications" / "Fathom.app")]
    else:
        apps = Path(env.get("XDG_DATA_HOME") or home / ".local" / "share") / "applications"
        plan.launchers = [("menu entry", apps / "fathom.desktop"), ("command", home / ".local" / "bin" / "fathom-app")]
    return plan


# ---- launcher contents (pure, tested on every OS) ---------------------------

def desktop_exec_arg(path: Path) -> str:
    """Quote a path for a desktop entry's Exec key (freedesktop Desktop Entry spec):
    backslash-escape the quoting characters, then apply the string escape for '\\',
    then double '%' so it isn't read as a field code (Copilot review, #56)."""
    text = str(path)
    for char in '\\"`$':
        text = text.replace(char, "\\" + char)
    return '"' + text.replace("\\", "\\\\").replace("%", "%%") + '"'


def desktop_entry(app: Path) -> str:
    return ("[Desktop Entry]\nType=Application\nName=Fathom\nComment=Know your data. Keep the evidence.\n"
            f"Exec={desktop_exec_arg(app)}\nTerminal=false\nCategories=Office;Development;\n")


def mac_info_plist() -> str:
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
            '<plist version="1.0"><dict>\n'
            '<key>CFBundleName</key><string>Fathom</string>\n'
            '<key>CFBundleDisplayName</key><string>Fathom</string>\n'
            '<key>CFBundleIdentifier</key><string>io.github.eraevous.fathom.launcher</string>\n'
            '<key>CFBundleExecutable</key><string>Fathom</string>\n'
            '<key>CFBundlePackageType</key><string>APPL</string>\n'
            '<key>CFBundleVersion</key><string>1</string>\n'
            '<key>LSMinimumSystemVersion</key><string>10.13</string>\n'
            '</dict></plist>\n')


def mac_launcher_script(app: Path) -> str:
    return f'#!/bin/sh\nexec {shlex.quote(str(app))} "$@"\n'


# PowerShell reads all five of these as a single quote, so each must be doubled
# inside a verbatim string, not only U+0027 (about_Quoting_Rules; e.g. a profile folder named O\u2019Brien).
PS_SINGLE_QUOTES = "'\u2018\u2019\u201a\u201b"


def ps_quote(value: object) -> str:
    text = str(value)
    for char in PS_SINGLE_QUOTES:
        text = text.replace(char, char * 2)
    return "'" + text + "'"


def windows_shortcut_script(target: Path, start_menu: Path, workdir: Path, owned: list[str] = ()) -> str:
    """PowerShell that writes each .lnk through the user's own WScript.Shell.

    Prints SAVED:<path> after each shortcut is saved and SKIPPED:<path> for an existing
    shortcut this installer didn't create, so partial results can still be recorded."""
    owned_list = ",".join(ps_quote(p) for p in owned) or "''"
    return ("$ErrorActionPreference='Stop';$w=New-Object -ComObject WScript.Shell;"
            f"$owned=@({owned_list});"
            "$desk=Join-Path ([Environment]::GetFolderPath('Desktop')) 'Fathom.lnk';"
            f"foreach($p in @({ps_quote(start_menu)},$desk)){{"
            "if((Test-Path -LiteralPath $p) -and -not ($owned -contains $p)){Write-Output ('SKIPPED:'+$p);continue};"
            "$s=$w.CreateShortcut($p);"
            f"$s.TargetPath={ps_quote(target)};$s.WorkingDirectory={ps_quote(workdir)};"
            "$s.Description='Fathom: know your data, keep the evidence';$s.Save();"
            "Write-Output ('SAVED:'+$p)}")


def shortcut_results(stdout: str) -> tuple[list[str], list[str]]:
    saved, skipped = [], []
    for line in (stdout or "").splitlines():
        line = line.strip()
        if line.startswith("SAVED:"):
            saved.append(line[6:])
        elif line.startswith("SKIPPED:"):
            skipped.append(line[8:])
    return saved, skipped


# ---- steps ----------------------------------------------------------------

def say(message: str) -> None:
    print("fathom-install: " + message, flush=True)


def run(args: list[str]) -> None:
    subprocess.run(args, check=True)


def read_manifest(plan: Plan) -> list[str]:
    manifest = plan.data / MANIFEST
    if not manifest.is_file():
        return []
    try:
        return list(json.loads(manifest.read_text(encoding="utf-8")).get("created", []))
    except (ValueError, AttributeError):
        return []


def write_manifest(plan: Plan, created: list[str]) -> None:
    """Record what this installer owns: earlier records are kept, so an upgrade that
    couldn't recreate a launcher still lets uninstall remove it (Copilot review, #56)."""
    owned = list(dict.fromkeys([*read_manifest(plan), *created]))
    plan.data.mkdir(parents=True, exist_ok=True)
    (plan.data / MANIFEST).write_text(json.dumps({"venv": str(plan.venv), "created": owned}, indent=2), encoding="utf-8")


def check_source(plan: Plan) -> None:
    if plan.wheelhouse:
        if not list(plan.wheelhouse.glob("fathom_guide-*.whl")):
            raise SystemExit("fathom-install: wheelhouse/ has no fathom_guide wheel; rebuild it with install/make_bundle.py")
    elif not (Path(plan.source) / "pyproject.toml").is_file():
        raise SystemExit("fathom-install: no wheelhouse/ and no Fathom checkout next to this folder; "
                         "download the whole repository or an offline bundle")


def bundle_python(plan: Plan) -> str | None:
    """The Python minor version an offline bundle's wheels were built for, if recorded."""
    marker = plan.wheelhouse / "bundle.json" if plan.wheelhouse else None
    if marker and marker.is_file():
        return json.loads(marker.read_text(encoding="utf-8")).get("python")
    return None


def matching_python(version: str, system: str) -> list[str] | None:
    if system == "windows":
        return ["py", "-" + version] if shutil.which("py") else None
    found = shutil.which("python" + version)
    return [found] if found else None


def ensure_bundle_python(plan: Plan, argv: list[str]) -> None:
    """Wheels are built for one Python version: rerun with that one, or explain."""
    wanted = bundle_python(plan)
    running = "%d.%d" % sys.version_info[:2]
    if not wanted or wanted == running:
        return
    command = None if os.environ.get("FATHOM_INSTALL_REEXEC") else matching_python(wanted, plan.system)
    if command is None:
        raise SystemExit(f"fathom-install: this offline bundle was built for Python {wanted}, and this is {running}. "
                         f"Install Python {wanted} for this user, or rebuild the bundle with Python {running}.")
    say(f"switching to Python {wanted} to match the bundle")
    env = dict(os.environ, FATHOM_INSTALL_REEXEC="1")
    raise SystemExit(subprocess.run(command + [str(Path(__file__).resolve()), *argv], env=env).returncode)


def venv_python_version(plan: Plan) -> str | None:
    try:
        done = subprocess.run([str(plan.python), "-c", "import sys; print('%d.%d' % sys.version_info[:2])"],
                              capture_output=True, text=True, check=True)
        return done.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def make_venv(plan: Plan) -> None:
    if plan.python.exists():
        running = "%d.%d" % sys.version_info[:2]
        if venv_python_version(plan) == running:
            say(f"upgrading the existing environment in {plan.venv}")
            return
        # Wheels match one Python version: rebuild an environment made by another (Codex review, #56).
        say(f"replacing the environment in {plan.venv}: it isn't Python {running}")
        shutil.rmtree(plan.venv)
    plan.data.mkdir(parents=True, exist_ok=True)
    say(f"creating a private Python environment in {plan.venv}")
    run([sys.executable, "-m", "venv", str(plan.venv)])


def _ours(path: Path, owned: set[str]) -> bool:
    """A launcher path is ours to write if it's free or an earlier install recorded it."""
    if not (path.exists() or path.is_symlink()) or str(path) in owned:
        return True
    say(f"left {path} alone: it already exists and this installer didn't create it")
    return False


def add_launchers(plan: Plan) -> list[str]:
    owned = set(read_manifest(plan))
    created = []
    if plan.system == "linux":
        entry, command = (path for _, path in plan.launchers)
        if _ours(entry, owned):
            entry.parent.mkdir(parents=True, exist_ok=True)
            entry.write_text(desktop_entry(plan.app), encoding="utf-8")
            created.append(str(entry))
            write_manifest(plan, created)  # recorded before the next step can fail (Copilot review, #56)
        if _ours(command, owned):
            try:
                command.parent.mkdir(parents=True, exist_ok=True)
                if command.is_symlink() or command.exists():
                    command.unlink()
                command.symlink_to(plan.app)
                created.append(str(command))
            except OSError as error:
                say(f"couldn't add {command} ({type(error).__name__}); use the menu entry or {plan.app}")
    elif plan.system == "macos":
        bundle = plan.launchers[0][1]
        if _ours(bundle, owned):
            macos = bundle / "Contents" / "MacOS"
            macos.mkdir(parents=True, exist_ok=True)
            (bundle / "Contents" / "Info.plist").write_text(mac_info_plist(), encoding="utf-8")
            launcher = macos / "Fathom"
            launcher.write_text(mac_launcher_script(plan.app), encoding="utf-8")
            launcher.chmod(0o755)
            created.append(str(bundle))
    else:
        start_menu = plan.launchers[0][1]
        start_menu.parent.mkdir(parents=True, exist_ok=True)
        script = windows_shortcut_script(plan.app, start_menu, plan.home, sorted(owned))
        try:
            done = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                                  capture_output=True, text=True)
            output, failed = done.stdout, done.returncode != 0
        except OSError:
            output, failed = "", True
        saved, skipped = shortcut_results(output)
        created += saved
        for path in skipped:
            say(f"left {path} alone: it already exists and this installer didn't create it")
        if failed:
            say("couldn't create every shortcut (PowerShell or WScript.Shell may be blocked here). "
                f"Start Fathom by double-clicking {plan.app}")
    return created


def install(plan: Plan, argv: list[str] = ()) -> int:
    ensure_bundle_python(plan, list(argv))
    if sys.version_info < MIN_PYTHON:
        raise SystemExit(f"fathom-install: Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer is needed; this is {sys.version.split()[0]}")
    check_source(plan)
    make_venv(plan)
    say("installing Fathom " + ("offline from " + str(plan.wheelhouse) if plan.wheelhouse else
                                "from " + plan.source + " (pip downloads pandas and PyYAML)"))
    run(plan.pip_args())
    if plan.reinstall_args():
        run(plan.reinstall_args())
    created = add_launchers(plan)
    write_manifest(plan, created)
    check = subprocess.run([str(plan.guide), "app", "--check"], capture_output=True, text=True)
    say("installed. Start it from: " + (", ".join(created) or str(plan.app)))
    say(f"command line: {plan.guide}")
    if check.returncode:
        say("the desktop window can't open with this Python:\n" + check.stderr.strip())
    say("reports go to " + str(plan.home / "Fathom") + " unless you choose another folder")
    return 0


def uninstall(plan: Plan) -> int:
    manifest = plan.data / MANIFEST
    created = json.loads(manifest.read_text(encoding="utf-8"))["created"] if manifest.is_file() else []
    for item in created:
        path = Path(item)
        if path.is_symlink() or path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
        say("removed " + item)
    if plan.venv.is_dir():
        shutil.rmtree(plan.venv)
        say("removed " + str(plan.venv))
    if manifest.is_file():
        manifest.unlink()
    if plan.data.is_dir() and not any(plan.data.iterdir()):
        plan.data.rmdir()
    say("done. Your reports in " + str(plan.home / "Fathom") + " were left in place.")
    return 0


def describe(plan: Plan, uninstalling: bool) -> int:
    if uninstalling:
        say(f"would remove {plan.venv} and the launchers listed in {plan.data / MANIFEST}")
        return 0
    wanted = bundle_python(plan)
    if wanted and wanted != "%d.%d" % sys.version_info[:2]:
        say(f"would switch to Python {wanted} to match the offline bundle")
    say(f"would create or upgrade {plan.venv} with {sys.executable}")
    say("would run: " + " ".join(plan.pip_args()))
    if plan.reinstall_args():
        say("would run: " + " ".join(plan.reinstall_args()))
    for label, path in plan.launchers:
        say(f"would add {label}: {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install Fathom for this user only (no admin rights).")
    parser.add_argument("--dry-run", action="store_true", help="print the plan; change nothing")
    parser.add_argument("--uninstall", action="store_true", help="remove what an install created")
    parser.add_argument("--extras", default="", help="comma-separated: " + ", ".join(EXTRAS))
    raw = list(sys.argv[1:] if argv is None else argv)
    args = parser.parse_args(raw)
    extras = tuple(e for e in (x.strip() for x in args.extras.split(",")) if e)
    unknown = [e for e in extras if e not in EXTRAS]
    if unknown:
        parser.error("unknown extras: " + ", ".join(unknown))
    plan = make_plan(system_name(), Path.home(), dict(os.environ), extras=extras)
    if args.dry_run:
        return describe(plan, args.uninstall)
    try:
        return uninstall(plan) if args.uninstall else install(plan, raw)
    except subprocess.CalledProcessError as error:
        say(f"stopped: a step failed (exit {error.returncode}): {' '.join(map(str, error.cmd))}")
        say("nothing outside your own folders was changed; fix the message above and run the installer again")
        return 1


if __name__ == "__main__":
    sys.exit(main())
