# Implementation Plan: Plots and layout

**Branch**: 005-plots-and-layout | **Date**: 2026-11-02 | **Spec**: [spec.md](spec.md)

## Summary / technical context

Existing Python3.12/pandas/PyYAML, pytest and optional SciPy/ReportLab/python-pptx.
No new runtime dependency. Local CLI, version1 JSON, offline HTML/SVG/Markdown and
optional PDF/PPTX. Bound plots/masks to avoid report explosions; no new pair methods.

## Constitution check (before/after design)

PASS: connector→wrapper→profiler→artifact→renderers retained; inferred/human basis
and typed findings/evidence preserved; no new pairs, comparisons still context-first;
exact tests/clean decoys/bytes/degradation; synthetic evidence only. Charter unchanged.

## Structure / sequence

Tests first in tests/test_plots_layout.py. univariate.py adds pure histogram/ECDF,
category remainder, text length, sensible date charts and exact row-mask summary;
profiler.py routes summary; models.py validates new optional fields. charts.py
renders ECDF/pattern SVG and adjacent labels. New presentation.py is a renderer
adapter for formatted statistic/frequency tables, shared by HTML/Markdown/PDF.
renderers.py composes full-width column entries; exports.py handles new chart kinds
using vector PDF and native numeric XY PPTX for ECDF. No renderer reads CSV.

## Review-only tooling / dependencies

Existing Playwright+Chromium for actual HTML screenshots; PyMuPDF/pypdf for actual
PDF rasterization/content, Pillow for contact sheets/image sizing. LibreOffice
Impress is preferred actual PPTX renderer (local extracted packages if no root);
if unavailable, a justified local office renderer can be used with limitations
recorded, never a mock of the exported slide. These are review tools, not project
runtime/test requirements. Commit bounded PNG evidence and reproduction script;
no source data outside authored fixtures. Reference public GOV.UK tables, Analysis
Function chart guidance, YData profiling docs; compare observed practices explicitly.

## Validation

Exact bin/share/mask/ECDF and date/time decoys; artifact validation, legacy render,
no-network/extras and fresh-process export bytes. Baseline/after all formats at
1280/390, visually inspect representative column/category/date/missingness and
export pages/slides, log fixes/open issues. Builder planted/clean/late acceptance.
AEC purpose/check/impact hooks; preserve original records/protected docs. Rebase
onto main after#10 merges; publish only after checks, stop when PR open.
