# How Fathom's usefulness is judged

**Status: proposed (2026-11-01, claude:aec). Zach accepts or changes it** (`FT-R4`, provisional).

Tests show that Fathom does what its spec says. They don't show that it helps. A feature counts as useful when it passes the criterion below on a table it wasn't developed against.

## The criterion

1. **Consequence:** *can the analyst understand something consequential about the dataset that the initial table did not make obvious, without Fathom pretending to know more than it does?* This is Kate's criterion, written during the prototype review.
2. **Standalone documentation (`DG-A1`):** *could someone who has never seen the table use the output as its documentation?* That means they could tell what each column holds, what looks wrong, and what nobody knows yet.

Both questions have to be answerable "yes" from the report alone, without opening the data.

## How to use it while building

- **Write your own acceptance tables.** Make synthetic tables with problems planted in them that the analyst should find. Use public datasets too, with their source stated. For each one, check the report against the planted list before calling a slice done. List what it found and what it missed in the PR.
- **A finding has to be in the report, not just in the statistics.** "max 999, mean 87, median 53" in the dictionary is not a finding. *"3.6% of `age` equals 999, its maximum; 999 may be a code for unknown"*, with a suggested action, is one.
- **Silence is not a pass.** A report with no findings on a messy table fails criterion 1, however correct its labels are.
- **Zach and Kate judge on tables you haven't seen.** Those tables are deliberately not in this repository.

## What it does not ask

- Domain explanations the table can't support. `DG-RB` still applies: a finding about meaning is a labelled hypothesis or a question.
- Completeness. A slice is judged on whether it surfaces consequential things, not on whether it surfaces everything.
