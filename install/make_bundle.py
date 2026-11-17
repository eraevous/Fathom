#!/usr/bin/env python3
"""Build an offline install bundle (spec 031). Standard library plus pip.

  python install/make_bundle.py [--extras stats,exports] [--out dist]

Run it on a connected machine with the SAME operating system, CPU architecture and
Python minor version as the machine that will install offline: wheels are
platform-specific. It writes dist/Fathom-<version>-<os>-<arch>-py<XY>.zip holding the
installers and a wheelhouse/ (Fathom and its dependencies). Unzip it on the target
and double-click the installer; nothing is downloaded there. Review the bundle and
move it by an approved route. Never commit a wheelhouse to the repository.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
INSTALLERS = ("Install Fathom.bat", "Install Fathom.command", "install-fathom.sh", "fathom_install.py")


def version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    return re.search(r'^version = "([^"]+)"', text, re.M).group(1)


def bundle_name(system: str, machine: str, python: tuple[int, int]) -> str:
    os_name = {"win32": "windows", "darwin": "macos"}.get(system, "linux")
    return f"Fathom-{version()}-{os_name}-{machine.lower()}-py{python[0]}{python[1]}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--extras", default="", help="comma-separated extras to include, e.g. stats,exports")
    parser.add_argument("--out", type=Path, default=ROOT / "dist")
    args = parser.parse_args(argv)
    name = bundle_name(sys.platform, platform.machine(), sys.version_info[:2])
    folder = args.out / name
    if folder.exists():
        shutil.rmtree(folder)
    wheelhouse = folder / "wheelhouse"
    wheelhouse.mkdir(parents=True)
    target = str(ROOT) + (f"[{args.extras}]" if args.extras else "")
    subprocess.run([sys.executable, "-m", "pip", "--disable-pip-version-check", "wheel", "--wheel-dir", str(wheelhouse), target], check=True)
    (wheelhouse / "bundle.json").write_text(
        '{"python": "%d.%d", "platform": "%s", "machine": "%s"}\n' % (*sys.version_info[:2], sys.platform, platform.machine()), encoding="utf-8")
    for item in INSTALLERS:
        shutil.copy2(ROOT / "install" / item, folder / item)
    shutil.copy2(ROOT / "install" / "README.txt", folder / "README.txt")
    archive = shutil.make_archive(str(folder), "zip", root_dir=args.out, base_dir=name)
    print(f"make_bundle: wrote {archive}; for {name.split('-', 2)[2]} only")
    return 0


if __name__ == "__main__":
    sys.exit(main())
