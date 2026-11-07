# Implementation plan — 024
Serves P0@2, FT-SERVE24-R1@1. Python3.12 stdlib http.server/socketserver/secrets/audit hook; existing pandas/PyYAML and configurator. No new dependency. Lazy server import preserves offline startup of every existing command.

Constitution gate: one connector/profiler/artifact path, existing CLI profile invoked in process; no analysis change or AI layer; provisional records before code; synthetic violations/decoys; deterministic reports. All pass. Drift check: a small bounded local transport is necessary for the explicitly authorized rerun; it has no service/plugin abstraction.

1. Specify request/security contract, append requirement, run AEC report-only precheck.
2. Add strict config-text entry point and loopback session/HTTP handler; validate config and output identities before writes; same profile composition.
3. Add lazy CLI command and live-only controls; static fallback stays offline.
4. Add independent real HTTP tests and extended offline denial harness, regression/clean decoys.
5. Full extras tests, screenshot actual session at both widths/themes, report byte comparison, append claim/evidence, regenerate edges/check/impact, open one PR off main for Kate first.
