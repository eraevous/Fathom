# Contract

Config additions: title, description (nullable text); sample_rows 0..100 default20;
sample_seed 0..2^32-1 default0; sample_text_limit 20..1000 default120. Column metadata
adds date_format (ISO, MON_D_Y, MDY, DMY), units (text), role (identifier/quantity).

CLI unchanged. HTML/Markdown start title/description then Dictionary, Provenance,
Dataset summary, Findings, Relations. Samples are dictionary disclosures; per-column
examples are visible. Technical internals and univariate numbers are disclosures;
charts have title/axes/units or counts. All views use saved artifact fields only.
