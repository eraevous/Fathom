# Install Fathom with one double-click, and use the desktop window

Spec 031. These steps install Fathom **for you only**. They need no admin rights and change no PATH, registry or shell profile. Fathom runs on your computer, and nothing it reads or writes leaves it.

## Install

You need **Python 3.11 or newer**.

| System | Do this | Python, if you don't have it |
| --- | --- | --- |
| Windows | Double-click `install/Install Fathom.bat` | [python.org](https://www.python.org/downloads/windows/): leave "Use admin privileges when installing py.exe" unticked and it installs for you only. |
| macOS | Double-click `install/Install Fathom.command` | [python.org](https://www.python.org/downloads/macos/). Its installer asks for an administrator password; if you have none, ask whoever manages the Mac. |
| Linux | `sh install/install-fathom.sh` | Your distribution's `python3.11` (or newer) and `python3-tk` packages. |

The installer creates a private environment, installs Fathom into it and adds a launcher:

| System | Environment | Launcher |
| --- | --- | --- |
| Windows | `%LOCALAPPDATA%\Fathom\venv` | **Fathom** in the Start menu and on the Desktop |
| macOS | `~/Library/Application Support/Fathom/venv` | `~/Applications/Fathom.app` |
| Linux | `~/.local/share/fathom/venv` | **Fathom** in the applications menu, and `~/.local/bin/fathom-app` |

The command line is in the same environment: `…\venv\Scripts\guide.exe` on Windows, `…/venv/bin/guide` elsewhere.

- **Upgrade:** run the installer again.
- **Preview:** `--dry-run` prints what it would do and changes nothing.
- **Remove:** `--uninstall` removes the environment and the launchers it created. Your reports in `~/Fathom` stay.
- **Optional extras:** `--extras stats,exports`.

### Where it gets the packages

- **From the repository download** (the default): pip installs Fathom from this folder and downloads `pandas` and `PyYAML` from the Python Package Index. If your network blocks that, use an offline bundle.
- **From an offline bundle:** if a `wheelhouse/` folder sits beside the installer, it installs from that folder with `--no-index`, and nothing is downloaded.

### Make an offline bundle

On a connected machine with the **same operating system, CPU type and Python version** as the target:

```bash
python install/make_bundle.py            # add --extras stats,exports if you want them
```

This writes `dist/Fathom-<version>-<os>-<cpu>-py<XY>.zip`, which contains the installers and a `wheelhouse/`. Review it, and move it by a route you're allowed to use. Then unzip it on the target and double-click the installer. If the bundle was built for a different Python version, the installer switches to that version when it's installed, and otherwise says which one is needed. CI builds one bundle per system for Python 3.12, kept for 14 days as a workflow artifact. Never commit a wheelhouse to the repository.

### When a security prompt appears

The installers are plain scripts you can read. They are not signed.

- **Windows:** SmartScreen may say "Windows protected your PC". Choose **More info**, then **Run anyway**. Some managed PCs block scripts or programs in your own folders entirely. If shortcuts can't be created, the installer says so and prints the path of `fathom-app.exe` to double-click instead.
- **macOS:** if Finder refuses the downloaded `.command`, open **System Settings → Privacy & Security** and choose **Open Anyway**. You can also run `sh "install/Install Fathom.command"` in Terminal. The `Fathom.app` it creates is made on your Mac, so it doesn't trigger the prompt.

## Use the desktop window

Open **Fathom** from the launcher, or run `guide app`.

1. **Choose…** a CSV. A config YAML is optional. The output folder defaults to `~/Fathom/<table name>/`.
2. **Quick look** runs `guide liftoff` and opens the brief: what the table shows, and the configurations you can choose.
3. **Profile** runs `guide profile` and opens the report.
4. **Configure in browser** starts the usual [local rerun session](local-reruns.md) on the chosen CSV and opens it. Edit the declarations there and click **Rerun**. **Stop browser session**, closing the window, or the page's own Stop control ends it.
5. **Recent reports** lists what's saved under `~/Fathom`. Double-click one to open it.

Each button runs the same command as the command line, in the same process, so the files are byte-identical to `guide liftoff`, `guide profile` and `guide serve`.

Reports can contain values from your table. If the CSV or the output folder is in a cloud-synced folder (OneDrive, Dropbox, iCloud and so on), the window warns you, because the files may be copied off the computer. `sample_rows: 0` is not redaction. Review outputs before you share them.

### If the window doesn't open

`guide app --check` reports whether this Python can show the window. Some Pythons ship without `tkinter`, including Homebrew's and minimal Linux builds. The message names the fix. Everything the window does is also a command:

```bash
guide liftoff DATA.csv --out DIR/liftoff
guide profile DATA.csv --config fathom.yaml --out DIR/profile
guide serve DATA.csv --config fathom.yaml --out DIR/working
```
