# Target-analysis fixtures

planted/clean/late CSVs are authored synthetic data; YAML fixes target, budget and
human declarations. No real contact/customer/employer data.

planted40x7: signal has a positive target relationship; the last3rows form a small
high-target group; other has missing values in that group. copy is a raw target copy,
record_id is unique, known_rank_leak is the exact ordinal target rank (ties broken
by input row) and is explicitly excluded in config as known leakage. clean40x7
balances signal and category against target, keeps complete other values, and
retains the copy/ID/config-excluded rank as screening decoys.

late24x5 was prepared after core implementation: categorical outcome is strongly
related to predictor, with rare group2rows; numeric decoy is balanced; hidden_signal
is the target encoded0/1 and is deliberately NOT marked as leakage. sometimes_missing
copies category values except for2missing entries. This tests the disclosed limit:
values alone cannot identify which strong associations are safe to use.

movies.yaml and college.yaml reference the existing pinned public CSVs in ../polish,
whose source URLs, conversion and hashes remain in ../polish/sources.json. They
only declare target and USD units. Those are presentation declarations for this
public review; no private data or network lookup is involved.
