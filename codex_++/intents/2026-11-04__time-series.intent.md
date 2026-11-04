# Intent: spec011 time series (claude:dg#timeseries)

1. Zach's four-dimension vocabulary (frequency, amplitude, wavelength, duration) is the structure;
   ADI and CV² appear only as aliases inside frequency and amplitude (Kate's proposal, accepted as a
   naming reading, not as a design authority).
2. Three kinds of absence are kept apart: value series distinguish missing observations (no row
   or no parsed value in the period) from explicit zeros; event series count empty periods as 0
   but call them "periods with no event" and ask whether the process was observed. Missing
   periods are excluded from ACF pairs (pairwise-complete), never imputed.
3. "Signal present" uses a Bonferroni family-wise band over the supported lags, not the per-lag
   95% band: with 28 lags the per-lag band alone flags white noise most of the time. Measured
   false-positive rate on 200 white-noise seeds: 8/200. The per-lag band is still drawn and tabled.
4. Lags > n/4 are computed and shown pale but excluded from dominant lags and from the signal.
5. Calendar lags (24/168 h, 7 d, 52 w, 12 m) are calendar arithmetic, not domain meaning.
6. `auto` = hour/day/week/month as resolution and span allow (2..100,000 periods); hour needs a
   time of day on every parsed timestamp. Narrower reading: no sub-hour granularity.
7. `by:` builds Zach's open question narrowly: top N groups by row count (default 5, max 20);
   the rest are counted. Whether the unit is one series or a collection is left to Zach.
8. Two granularities charted: most supported lags outside the family band, then larger n.
9. The undeclared question fires whenever a temporal and a numeric column coexist and nothing is
   declared; it is one question line and names the columns. If this proves noisy, Zach decides.
10. Commit attribution uses the session's model line (Opus 5.5) as in the system attribution
    reminder; the launching message asked for a different model name, which would misattribute.
