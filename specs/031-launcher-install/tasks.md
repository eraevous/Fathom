# Tasks: 031 desktop launcher and one-click per-user install

- [x] T001 Spec with constraints and boundaries (`spec.md`); dissent review by a fresh-context reviewer, folded into the spec and PR #56
- [x] T002 Provisional records `FT-APP31-R1`, `-C1`, `-E1`; intent note
- [x] T003 `serve.serve_until_stopped` (one loop for CLI and launcher) and `serve.PROFILE_LOCK`; existing serve tests unchanged and passing
- [x] T004 `fathom.app`: `run_cli`, `quick_look`, `profile`, `ServeSession`, `recent_reports`, `default_output`, `synced_location`, `check`
- [x] T005 `fathom.app_window`: Tk window, worker threads, queue to main thread, Stop on close
- [x] T006 `guide app [--check]`; `fathom-app` GUI script; missing tkinter exits 2 with the fix
- [x] T007 Installer: plans for Windows, macOS, Linux; venv; pip online or offline; launchers; manifest; dry run; uninstall keeps reports
- [x] T008 Offline bundle (`make_bundle.py`, `bundle.json`); installer switches to the bundle's Python; a venv from another Python is rebuilt (Codex review, #56)
- [x] T009 Wrappers for each OS; Windows `.bat` with CRLF and no admin steps
- [x] T010 Tests: `tests/test_launcher.py`, `tests/test_installer.py` (Tk tests under a display)
- [x] T011 CI `install` job on ubuntu, macOS and Windows, with bundle artifacts
- [x] T012 Docs: `docs/install.md`, README install section and command table
- [ ] T013 Zach: double-click install on a managed Windows PC and on a Mac; decide on the GUI scope and `FT-APP31-R1`
