# Intent: spec 035 slice 3 (linear and tree families: L1, L2, L3, E1, E2, E3)

Author: claude:fathom#wake-20261124-17 · Reviewer: none yet · model=claude-opus-5-5

Where the spec is silent, I took the narrower reading. Each item is the implementer's reading (unconfirmed), for Zach to adjust:

1. **L1's 12-feature cap takes the first 12 numeric features in feature order**; the rest are listed under `not_evaluated`. No ranking or selection is done to choose which 12 (CHARTER 4).
2. **L1's thresholds are fixed constants**: a feature is dependent when its orthogonalized remainder keeps less than 1e-6 of its standardized variance (the same tolerance spec 034 slice 2a uses for collinear controls); the condition number fires at 30 and a variance inflation factor is named at 10. These are the conventional rules of thumb, printed in the registry; they are not a verdict. The condition number and VIFs are computed only when the design has full rank.
3. **L1 uses complete rows only** (every design feature parses as a number) and needs at least 30 of them and at least two numeric features; otherwise `insufficient_data`.
4. **L2 and E1 compute the same level counts** and differ in family, framing and wording. A Boolean feature's spellings are case-folded, as T1 does; missing cells are not a level; identifier features are not evaluated.
5. **L3 reports every pure level**, including small ones: with indicator coding a one-row level also separates its class. L2 names the small ones separately. Numeric separation is one class against all others; with two classes it is reported once.
6. **E2's distinct-share rule applies only to features not read as numeric**, and only over at least 30 present cells. Many distinct measurements are not memorisation; numeric features are judged by the identifier role alone.
7. **E3's thresholds**: a gap of at least 0.10 in missing share between classes that each have 30 or more rows; for regression and count, a target-mean gap of at least 0.2 target standard deviations with 30 or more rows on each side. Forecast is not covered (spec 035 slice 4's T5/S1–S3 handle time).
8. **No family limit text yet.** "Every family section opens with its limit" is a rendering concern; it comes with the dedicated HTML section.
9. **Stacked on #81** (DEC-261: #81 has a Codex review with no findings on 643841a), which is stacked on #77. Two deep, the limit. If either changes, this branch is rebased.
