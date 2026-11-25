# Intent: spec 035 slice 2 (split and entity: W2, W3, W4, T2, T4, E4)

Author: claude:fathom#wake-20261124-13 · Reviewer: none yet · model=claude-opus-5-5

Where the spec is silent, I took the narrower reading. Each item is the implementer's reading, for Zach to adjust:

1. **Split sides match the stored text exactly.** A row is train or evaluation only when its split value equals one of the declared values; anything else (including empty) is counted as `outside_split` and left out of every split check.
2. **W2 groups on features only.** The spec's "(or whose entity)" is covered by W3, which needs `entity`; W2 doesn't fold entity into its key, so the two checks stay separable.
3. **W4 reads dates strictly.** ISO dates and date-times, and other spellings `parse_date` reads one way only. A day/month-ambiguous value (03/04/2026) is counted as undated rather than guessed.
4. **W4's overlap window** is earliest evaluation date to latest train date, shown only when the check fires.
5. **T2's condition looked for** is a class present on one side only. Classes under 30 rows per side are named in the table but don't fire T2 on their own (T1 already names small classes).
6. **E4 is a tree-family check** and runs only when `families` includes `tree`. Numeric features are compared to the train range; categorical and Boolean features by unseen levels; text, date and identifier features are listed as not evaluated.
7. **Questions for roles** follow the slice 1 rule: every missing role a task-allowed check needs is asked for once, with the checks it unlocks. With no split declared, both `split` and `entity` are asked (W3 needs both).
8. **Stacked on #77** (DEC-261: #77 has a Codex review with no findings on 48e8e4a). If #77 changes, this branch is rebased.
