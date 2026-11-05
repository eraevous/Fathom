# Tasks
- [ ] T001 Record scope and baseline in specs/015-headlines-and-gates/review/.
- [ ] T002 [US1] Test headline cap/order/conditional labels in tests/test_headlines.py.
- [ ] T003 [US2] Test failed/passed contrast and skew gates in tests/test_headlines.py.
- [ ] T004 [US2] Add gate evidence in src/fathom/target.py and src/fathom/quality.py.
- [ ] T005 [US1] Render headlines/gates in src/fathom/renderers.py and src/fathom/liftoff.py.
- [ ] T006 Validate offline/reproducibility and screenshots; append evidence, open PR.
Dependencies: T001→T002/T003→T004→T005→T006. Independent test fixture reads can run
in parallel; edits remain sequential. Smallest useful increment: both report claims
and their inline explanations, without changing verdict logic.
