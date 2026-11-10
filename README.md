<p align="center"><img src="docs/assets/fathom-banner.svg" alt="Fathom. Understanding before modelling." width="880"></p>

<p align="center"><b>Know your data. Keep the evidence.</b><br>A local data dictionary, diagnostic EDA tool and repeatable working record.</p>

<p align="center"><a href="docs/index.html">Landing page source</a> · <a href="docs/guide.md">User guide</a> · <a href="docs/demo-report.html">Synthetic report source</a> · <a href="#try-it-in-five-minutes">Quick start</a> · <a href="#what-works-today">Capabilities</a></p>

Fathom helps you understand what a table contains, what needs review and what it cannot tell you. It keeps observations, interpretations, hypotheses, suggested actions and questions separate, with their evidence attached.

**Working prototype · Python 3.12+ · MIT · Local-first.** Package: `fathom-guide`. Command: `guide`. Install from this repository; it is not on PyPI. Open `docs/index.html` locally for the landing page and working synthetic demo. No hosted site is assumed.

## Try it in five minutes

```bash
git clone https://github.com/eraevous/Fathom.git
cd Fathom
python -m venv .venv
# macOS / Linux
.venv/bin/pip install -e '.[test]'
.venv/bin/guide profile tests/fixtures/review.csv --config tests/fixtures/review.yaml --out reports/first
# Windows PowerShell: use .venv\Scripts\pip.exe and .venv\Scripts\guide.exe instead.
```

Open `reports/first/report.html` in your browser. The input is synthetic. Its missing value and repeated row produce review questions, not automatic deletion or imputation.

Each run saves **`guide-profile.json`**, **`report.html`** and **`report.md`**. The JSON is the authoritative artifact. Shareable views can be regenerated from it without reopening the source CSV.

### Discover, declare, review

```bash
guide liftoff data.csv --out discovery --yaml fathom.yaml
guide profile data.csv --config fathom.yaml --out report
# Optional browser workflow, on the same machine:
guide serve data.csv --out working
```

Use the installed `guide` path above, or activate the virtual environment first. Liftoff separates observed facts from conditional previews. Its untouched YAML is `{}`: suggestions apply only when you select them. `serve` prints a session-specific URL; keep it private. It binds only to `127.0.0.1`, expires when idle, and provides a Stop control. [Local rerun boundaries →](docs/local-reruns.md)

## What works today

| Capability | What you get |
| --- | --- |
| **Dictionary and univariate EDA** | Labelled type inference and overrides, completeness, examples, distributions, quantiles and static plots. |
| **Quality review** | Missingness, repeated rows, duplicate/lockstep columns, suspicious values, date gaps and other bounded heuristics with evidence and limitations. |
| **Target-aware relationships** | Budgeted numeric/categorical associations, group summaries, sample counts, exclusions and cautions. Descriptive, not causal. |
| **Temporal structure** | Declared event/value series, sparsity, zero runs, ACF/PACF and optional periodograms. Missing observations, explicit zeros and unrecorded periods stay distinct. |
| **Long panels** | Explicit series keys, time/value/exposure/state, training/evaluation windows, separate aggregates and metric comparisons through `guide panel`. |
| **Local configuration** | Liftoff and a browser YAML editor, identifier roles, portable date/clock definitions, plus authenticated local reruns. |
| **Repeatable handoff** | Context-first before/after comparisons; saved JSON → HTML/Markdown; optional PDF, PowerPoint and tidy CSV exports. |

See the [full guide](docs/guide.md), [identifier documentation](docs/identifiers.md), [temporal formats](docs/temporal-formats.md), [clock fields](docs/time-definition.md) and [tidy export contract](docs/tidy-export.md).

## Pick a command

| I want to… | Command |
| --- | --- |
| See a first-pass brief and choose declarations | `guide liftoff DATA.csv --out discovery` |
| Edit configuration offline | `guide configure DATA.csv --out configure` |
| Rerun from a local browser | `guide serve DATA.csv --out working` |
| Profile a table / check its declared contract | `guide profile DATA.csv --out report` / `guide validate DATA.csv` |
| Compare two saved profiles | `guide compare BEFORE.json AFTER.json --out comparison` |
| Rebuild a report without the CSV | `guide render PROFILE.json --out rendered` |
| Profile an explicitly declared panel | `guide panel LONG.csv --config panel.yaml --out panel` |
| Export saved measurements | `guide export PROFILE.json --out exports` or `--tidy tidy` |

Install optional serializers with `pip install -e '.[exports]'`, or statistics with `pip install -e '.[stats]'`. Missing extras are reported rather than crashing. [Offline installation →](docs/guide.md#offline-installation-and-panel-profiling)

## Know the boundaries

- Current source intake is one local CSV at a time, with a separate declared long-panel path. No general Excel, JSON, database or knowledge-base connector is included here.
- Fathom is in-memory and does not clean your data, establish causation, train a model or invent domain meaning. Rules can miss real problems and flag valid values.
- No telemetry or remote lookup is performed. Ordinary commands and reports work offline. `serve` uses local loopback only, not a multi-user hosted service.
- Reports and JSON can contain source values in examples, frequencies and evidence. **`sample_rows: 0` is not redaction.** Review outputs before sharing them.
- Identical inputs, paths, configuration and dependencies produce repeatable artifacts. PDF/PPTX repeatability also depends on serializer versions. Tidy CSV is a convenience view, not a lossless replacement for JSON.
- Tests establish behavior on their fixtures. Broad business fitness and usefulness remain matters for review.

## Develop and review

```bash
.venv/bin/python -m pytest -q
.venv/bin/python scripts/build_showcase.py
```

Fathom is built with [AEC](https://github.com/eraevous/AEC) and Spec Kit. Read [AGENTS.md](AGENTS.md), [CHARTER.md](CHARTER.md), the accepted records in `.aec/records.jsonl` and the [acceptance criteria](docs/acceptance.md) before changing it. The archived Data Guide implementation is not a source for this project.

Fixtures must be synthetic or documented public data. Never commit private reports, credentials or employer material. Work on a branch; owner acceptance is separate from passing tests or merging code. Contributions use the [CLA](CLA.md). [MIT license](LICENSE).
