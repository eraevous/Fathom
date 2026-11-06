# Local configuration reruns

`guide serve DATA.csv --out DIR [--config fathom.yaml]` prints a local URL. Open that exact URL on the same machine, edit the existing configuration controls and click **Rerun with this configuration**. The page shows the saved standalone report below the controls. Download/copy YAML still works. No browser is launched automatically.

The startup CSV and output directory stay fixed. Requests contain YAML declarations only, not paths, commands or uploads. Profiling runs in this process through the ordinary `guide profile` path. `report.html`, `report.md` and `guide-profile.json` match that command's bytes for the same CSV/config. The fixed additional files are `server-config.yaml` (latest submitted declarations) and `serve.log` (last 200 fixed activity labels). Reports contain no session token and work after the server stops.

The listener binds **127.0.0.1 only**, on an OS-allocated port; alternate hosts are refused. Every request needs the random session token and exact Host. Any Origin must match the local origin; POST requires it. Keep the terminal URL local: its token authorizes this session. A Python audit guard disallows non-loopback socket addresses and DNS lookups. HTTP responses forbid external resources and cross-origin fetches; no CORS is enabled. This is a local single-user workflow, not authentication between accounts on one machine.

**Stop local server** closes the listener. Ctrl+C also stops it. Idle expiry is 1,800 seconds (30 minutes), adjustable with `--idle-timeout SECONDS`. Nothing installs a service or needs admin permission. Windows firewall-dialog behavior has not been tested on Windows.

Without a running server, use the standalone configurator's copyable command:

```bash
guide profile DATA.csv --config fathom.yaml --out DIR
```

With JavaScript off, the page remains readable and explains this fallback; use Ctrl+C to stop. No live rerun control is added to saved report/configurator files.
