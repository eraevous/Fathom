# Intent: desktop launcher and one-click per-user install (spec 031)

- **The native window chooses files; the browser page stays `guide serve`.** A browser can't give a loopback server a local path without an upload or a path parameter, and spec 024 rules out both. A tkinter window (standard library) gets the path from the OS dialog and starts the unchanged session. This is the narrower reading of "both".
- **One session loop.** `run()`'s loop moved into `serve.serve_until_stopped`, so the CLI and the launcher thread share Stop, idle expiry and close. That avoids a second copy of the lifecycle (dissent review, risk 5).
- **One lock for captured output.** `redirect_stdout` and `redirect_stderr` are process-wide. Launcher runs and serve reruns take `serve.PROFILE_LOCK`, so their messages can't cross (dissent review, risk 1).
- **The installer is a script, not a binary.** It uses the standard library and `pip`. Nothing prebuilt is signed or shipped. The Windows shortcuts come from the user's own `WScript.Shell`, and if that's blocked the installer prints the program path instead.
- **Offline means a wheelhouse that contains Fathom's own wheel.** That way no build backend is needed on the target. `bundle.json` records the Python version, because wheels are version-specific. The installer reruns itself with that version, or explains which one it needs.
- **No bundled Python, and no macOS no-admin path.** Bundling an interpreter is a size, signing and policy decision. A Mac with neither Python 3.11+ nor admin is out of scope until Zach decides otherwise.
- **The workspace is `~/Fathom`, not Documents or Desktop.** On Windows those two are often redirected to OneDrive. The window still warns when a chosen path looks cloud-synced, because reports can hold table values.
- **Two things are for Zach:**
  - whether a GUI belongs beside the "thin CLI" in `docs/design.md`;
  - whether to accept `FT-APP31-R1`.
