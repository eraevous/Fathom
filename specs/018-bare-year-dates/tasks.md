# Tasks
- [x] T001 Record provisional requirement and scope in .aec/records.jsonl and intent.
- [x] T002 [US1] Add parser/numeric decoy/annual series/panel controls in tests/test_years.py.
- [x] T003 [US2] Add failed-format suggestion/no-match controls in tests/test_years.py.
- [x] T004 [US1] Wire YEAR into parsing.py/config.py/timeseries.py/panel.py/panel_stats.py.
- [x] T005 [US2] Add saved/report/CLI diagnostics in profiler.py/cli.py/target.py.
- [x] T006 [US1] Preserve coarse precision in univariate.py/presentation.py and #28 coverage.
- [x] T007 Full/offline suite after final records, screenshot/AEC review, open one PR.
Dependencies:T001→T002/T003→T004/T005→T006→T007. Independent fixture tests can run
together; source mutations sequential. No unresolved research or design question.
