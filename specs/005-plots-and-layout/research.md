# Research and decisions

Static column composition avoids premature dynamic UI. ECDF uses numerical XY
geometry, not category spacing. Exact row masks avoid pair/group analysis. A shared
presentation adapter keeps raw nested JSON away from main human views while
preserving raw disclosures and export consistency. No charting runtime added.

Review references: [GOV.UK tables](https://design-system.service.gov.uk/components/table/)
for scan-friendly numeric alignment; [Analysis Function charts](https://analysisfunction.civilservice.gov.uk/policy-store/data-visualisation-charts/)
for labels, scales, simple marks and text alternatives; [YData profiling](https://docs.sdk.ydata.ai/latest/getting_started/profiling/)
for per-variable statistics/distribution context. Specific visual comparisons and
limitations are recorded after rendering, not treated as product requirements.
