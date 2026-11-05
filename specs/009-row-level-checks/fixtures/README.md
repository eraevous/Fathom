# Authored synthetic row-check tables

All eight CSVs are newly authored synthetic values; geographic phrases are label cues,
not measurements or asserted row units. No held-out tables or private artifacts copied.
No seed needed: generation used fixed loops; committed CSVs are the inputs.

| Plant / clean decoy | Planted truth | Clean counterpart |
| --- | --- | --- |
| empty-values.csv / empty-values-clean.csv |9of18rows blank in all3year columns; metadata present | Every row has a value; literal0is retained |
| mixed-units.csv / mixed-units-clean.csv |5of12labels match listed regional phrases | No cue labels |
| repeated-key.csv / repeated-key-clean.csv |210keys×4rows; hinc/psize constant within, varying between; exactly one choice=1/key |840unique keys |
| zero-concentration.csv / zero-concentration-clean.csv |210zeros, all atmode4;4groups×210rows | Same210zeros distributed53/53/52/52 |

The repeated-key plant also has concentrated zeros; checks may share evidence but
must remain observation/question-only. The unique-key decoy is clean for repetition,
not all possible checks. These are declared truths, not app test passes.

Run `python specs/009-row-level-checks/verify_fixtures.py`: verifies the literal
[truth.json](truth.json) manifest independently of a future implementation.
