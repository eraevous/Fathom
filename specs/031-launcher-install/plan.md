# Plan: 031 desktop launcher and one-click per-user install

Spec: [spec.md](spec.md). Serves: P0@2. Must not break DG-RE@1 or DG-RF@1. Requirement `FT-APP31-R1` (provisional, for Zach).

## Approach

| Part | Where | How |
| --- | --- | --- |
| Launcher logic | `src/fathom/app.py` | Calls `cli.main` in this process for liftoff and profile under `serve.PROFILE_LOCK`. `ServeSession` wraps `serve.create_server` and runs `serve.serve_until_stopped` on a thread. Also holds the default output folder, recent reports, synced-folder detection and `--check`. |
| Window | `src/fathom/app_window.py` | tkinter and ttk. Worker threads post to a queue; only the main thread touches Tk (`after` polling). |
| CLI | `src/fathom/cli.py` | `guide app [--check]`. tkinter is imported lazily; without it, exit 2 with the fix. |
| Entry point | `pyproject.toml` | `[project.gui-scripts] fathom-app` (no console on Windows). |
| serve | `src/fathom/serve.py` | Extract the loop into `serve_until_stopped`, add `PROFILE_LOCK`. No new options, routes or request inputs. |
| Installer | `install/fathom_install.py` | Standard library: plan, venv, pip, launchers, manifest, `--dry-run`, `--uninstall`, `--extras`. Switches to the offline bundle's Python version, and rebuilds a venv from another version. |
| Wrappers | `install/Install Fathom.bat`, `Install Fathom.command`, `install-fathom.sh` | Find Python 3.11+, run the installer. CRLF for `.bat` (`.gitattributes`). |
| Offline bundle | `install/make_bundle.py` | `pip wheel` of Fathom + dependencies, `bundle.json`, zip. |
| Docs | `docs/install.md`, README | Install, offline, security prompts, the window, fallback commands. |
| CI | `.github/workflows/tests.yml` `install` job | ubuntu/macos/windows: launcher and installer tests (Xvfb on Linux), bundle, offline install, `guide app --check`, profile, uninstall, artifact. |

## Dependencies

None added. `tkinter`, `venv`, `subprocess`, `webbrowser` and `threading` are standard library. `pip` is only used by the installer and bundle scripts, outside the package. The test extra is unchanged. GitHub's own `actions/upload-artifact@v4` is CI only.

## Risks and choices

See `codex_++/intents/2026-11-17__launcher-install.intent.md` and the dissent review in PR #56:
- the narrower serve reading;
- one loop;
- one output lock;
- no bundled Python;
- macOS without admin is out of scope;
- unsigned scripts.

## Verification

- `tests/test_launcher.py` and `tests/test_installer.py`, plus the full suite.
- `aec check`.
- The CI `install` job on three operating systems.
- A manual offline install on Linux.
- The manual double-click on a managed Windows PC and on a Mac is left for Zach.
