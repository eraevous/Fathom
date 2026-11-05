# Local CLI and configuration
guide panel LONG.csv --config panel.yaml --out DIR [--aggregate week,month]
Required YAML keys: series (list of column names), time, value, period(day/week/month).
Optional: exposure, observation_state (column names); aggregation {rule: sum|mean,
group_by: [columns]}; windows (CSV path); metrics {path, columns:[names], targets:[names]};
thresholds [{name,value,per_days}]. No volume defaults. Paths resolve relative to YAML.
Windows CSV: series-id columns,model,train_start,train_end,eval_start,eval_end;
optional window and horizon. Missing window is deterministic bounds text. Keys unique.
Metrics CSV: series-id columns,model,window,optional horizon and declared metrics.
An optional metrics horizon fans out only unique observed horizon keys and is disclosed.
Observation-state values: observed,missing,closed. Blank observed values are missing.
Closed rows require absent/zero value and absent/zero exposure. Invalid values are errors.
Dates are strict YYYY-MM-DD; period start is calendar-floored. Duplicate series/period
rows fail. Windows use inclusive dates; monthly/weekly input rows must represent their
entire calendar bucket; native windows must align to those buckets. Daily windows may
end mid-coarse-bucket; view buckets are then partial and ineligible.
Output native panel.json/html/md + series-signals.csv; views/{week,month}/ own
artifacts and signal CSV; view-comparison.csv; joined-signals.csv; metric-disagreement.csv;
targets/<index>/guide-profile.json,report.html,report.md for chosen metrics.
render accepts panel artifacts. export panel Office formats is not added; use CSV/HTML.
Errors produce no partial output directory. Resource caps disclosed, fail rather than omit.

