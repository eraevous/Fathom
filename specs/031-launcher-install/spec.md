# 031: Desktop launcher and one-click per-user install

Owner request, Zach 2026-11-17: "Can we get a 1-click install for Fathom? Also a GUI interface?" Clarified the same day: Windows, macOS and Linux; the GUI is **both** a native window and the existing browser page; build it as a PR.

Proposed for Zach. Serves: P0@2 (Fathom can't help on a machine where it can't run). Must not break DG-RE@1 (the artifacts stay the CLI's, byte for byte) or DG-RF@1 (no tkinter → a message, not a crash). No accepted record covers distribution or a second interface (`docs/design.md` names a thin CLI), so requirement `FT-APP31-R1` is appended as provisional, for Zach. New subsystem: dissent review in the PR description (AGENTS Drift).

## Constraint carried in

Fathom must run per-user with **no admin rights** and **no data leaving the PC** (lane seed). So: no system-wide install, no service, no registry writes beyond the user's own shortcuts, no network in the app, and an offline install path.

## US1: Install with one double-click (P1)

- `install/` holds one thin wrapper per OS, each of which finds Python 3.11+ and runs the shared `install/fathom_install.py`:
  - Windows: `Install Fathom.bat` (double-click). It calls `py -3`, or `python` when that is 3.11+ (the Microsoft Store alias fails the check). If neither is found, it says so and names the per-user python.org installer, which needs no admin when its py.exe box is left unticked.
  - macOS: `Install Fathom.command` (double-click opens Terminal).
  - Linux: `install-fathom.sh`.
- `fathom_install.py` (standard library only):
  1. Creates a private virtual environment in the user's data folder: `%LOCALAPPDATA%\Fathom` on Windows, `~/Library/Application Support/Fathom` on macOS, `$XDG_DATA_HOME/fathom` (default `~/.local/share/fathom`) on Linux.
  2. Installs Fathom into it. If a `wheelhouse/` folder sits beside the installer, it installs **offline** (`--no-index --find-links`). That folder must hold a Fathom wheel, so no build step (and no setuptools) is needed offline. Otherwise it installs from the repository checkout, and pip fetches `pandas` and `PyYAML` from the package index.
  - `install/make_bundle.py` builds the offline zip (installers + wheelhouse + `bundle.json` naming the Python version). Wheels are per OS, CPU and Python version: the installer reruns itself with the bundle's Python if it's installed, or names the one it needs. CI builds one bundle per OS (Python 3.12) as a workflow artifact. A wheelhouse is never committed.
  3. Adds a launcher: a Start Menu and Desktop shortcut on Windows (through the user's own `WScript.Shell`, no admin), a `~/Applications/Fathom.app` on macOS, and a `.desktop` entry plus `~/.local/bin/fathom-app` on Linux.
  4. Prints what it did and where. `--dry-run` prints the plan and changes nothing; `--uninstall` removes exactly what it created; `--extras stats,exports` adds the optional extras.
- Re-running upgrades in place. Nothing outside the user's own folders is touched.

## US2: A desktop window (P1)

- `guide app` (also the `fathom-app` GUI entry point, with no console window on Windows) opens a small native window built with `tkinter` (standard library, no new dependency):
  - **Choose CSV…** opens the OS file dialog. **Config (optional)** chooses a YAML file. The **Output folder** defaults to `<home>/Fathom/<csv name>/` and can be changed.
  - **Quick look** runs `guide liftoff` into `<output>/liftoff` and opens `liftoff.html`.
  - **Profile** runs `guide profile` into `<output>/profile` and opens `report.html`.
  - **Configure in browser** starts the existing `guide serve` session on the chosen CSV, writing to `<output>/working`, and opens its private URL. **Stop** ends it. Closing the window stops it too.
  - **Recent reports** lists the report folders under `<home>/Fathom`, newest first. **Open** opens one.
  - A status line shows what's running and Fathom's own messages. Errors are shown, never swallowed.
- Every action is an ordinary CLI call in-process (`fathom.cli.main`), so the artifacts are byte-identical to the command line's. Captured output uses process-wide redirection, so launcher runs and serve reruns share one lock (`serve.PROFILE_LOCK`) and never interleave. Work runs on worker threads, and only the main thread touches Tk.
- If the CSV or the output folder looks cloud-synced (OneDrive, Dropbox, iCloud, Google Drive, Box), the window warns that reports with table values may leave the computer.
- Without `tkinter` (some Homebrew or minimal Linux Pythons), `guide app` exits 2 with a message that names the fix and the equivalent commands. It degrades, it does not crash (DG-RF).

## US3: The browser page stays the browser page (P1)

- The browser half of the GUI is the existing `guide serve` page, unchanged: loopback only, a session token, no request paths, no uploads. The native window does the file choosing, because a browser can't hand a local path to a server without an upload or a path parameter, and adding either would widen `serve`'s security model (spec 024). This is the narrower reading, and it is recorded in the intent note.
- `serve.create_server` gains no options. The session loop moves into `serve.serve_until_stopped`, which both `guide serve` and the launcher's background thread call, so there's one lifecycle (Stop, idle expiry, close). The launcher stops it with the same flag the Stop button sets. The process-wide network guard stays on in the launcher from start-up.

## Boundaries

- Not code-signed and not notarised. Windows SmartScreen may ask (More info → Run anyway). On macOS the downloaded `.command` may need System Settings → Privacy & Security → Open Anyway (recent macOS has dropped the right-click → Open bypass), or `sh` from Terminal. The installer is a script anyone can read; no `.exe` or `.app` is shipped prebuilt. The macOS `.app` is generated locally, so it carries no quarantine flag. Managed PCs (AppLocker, WDAC, ASR) may block programs in the user's folders entirely. If shortcuts fail, the installer prints the program path instead.
- No bundled Python. A machine without Python 3.11+ needs it first. On Windows, the python.org installer works per-user without admin. On macOS it needs an administrator password, so a Mac with no Python 3.11+ and no admin is **out of scope** unless Zach decides otherwise. A bundled interpreter is a larger decision (size, signing, AppLocker), left for Zach.
- The installer does not touch PATH, the registry (other than `.lnk` files in the user's own folders) or shell profiles.
- Tested on Linux here. Windows and macOS are exercised in CI (`install` job: install from the checkout, `--dry-run`, `--uninstall`, and a headless `guide app --check`). A double-click on a real Windows or Mac desktop is still a manual check for Zach.

## Tests

`tests/test_launcher.py` and `tests/test_installer.py`: per-OS paths and shortcut contents (pure functions, all three OSes); dry run changes nothing; install then uninstall into a temporary home with a local wheelhouse (offline); default output folders and the recent-report list; the launcher's actions produce the same bytes as the CLI; the serve session starts and stops from a thread; `guide app` without `tkinter` exits 2 with the message; a Tk smoke test that builds the window under a display (skipped without one).
