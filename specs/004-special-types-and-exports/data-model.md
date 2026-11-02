# Additions

Type enum adds phone/email/url/latitude/longitude. Inference/overrides remain distinct.
Column.special contains policy, valid/invalid counts, invalid examples, placeholder/
test counts/examples and common domains where relevant. Range checks assume degrees
and label that reading. Findings keep rule/generator/evidence/uncertainty/provenance.

Export bundle: core report views; optional report.pdf/report.pptx bytes; versioned
export-status.json with input-artifact hash, per-format status/dependency/limitations.
No source table re-read, new model inference, profile mutation or hidden remote link.
