# 024 — Loopback configuration reruns

Serves: P0@2, DG-RE@1, DG-RF@1, FT-SERVE24-R1@1.
Status: proposed for Zach; HO-DG-20261106-8RZJ, item C.

An analyst runs `guide serve DATA.csv --out DIR [--config CFG]`, opens the printed local URL, changes the existing configuration controls and reruns the ordinary profile without a second terminal command. The data and output paths remain fixed for the session. Reports remain standalone, deterministic files and the static configurator keeps its copyable CLI fallback.

## Acceptance
- Bind exactly 127.0.0.1 on a randomly allocated port; refuse other host bindings. Every request requires a random session token, exact Host, and any Origin must match; state-changing requests require Origin.
- Accept bounded YAML configurations only, validated by the ordinary strict config parser; no uploads, commands or requested filesystem paths. Run the same in-process profile command using startup-fixed paths, writing only into the fixed output directory.
- Enforce loopback-only network use, and independently test a real session with external sockets blocked. No installation, service, admin permission, external assets or runtime dependency.
- Stop button closes the server. Idle timeout is 1,800 seconds by default. Terminal prints URL and a bounded local activity log omits tokens/configuration/data.
- Report HTML/Markdown/JSON match the ordinary CLI for the same input/config, across reruns. Saved HTML needs no server; no live rerun button is exposed there.
- Regression fixtures include hostile tokens, hosts, origins, body/path/config payloads, output symlinks and clean authenticated reruns. Review actual local pages at 1280/390 in both themes.

No new analysis rules, panel mode, uploads, remote access or Windows service integration. Real Windows firewall behavior remains untested in this Linux build.
