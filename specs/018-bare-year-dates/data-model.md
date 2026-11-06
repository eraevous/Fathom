# Additive interface
parse_date YEAR returns Jan1 with precision year. Temporal statistics can carry
parse_failure formats/matches/suggestions; existing valid/invalid counts are unchanged.
Panel configuration optionally declares date_format:YEAR, period:year. Internal
periods stay ISO starts; windows retain ISO start/end bounds. Annual spectrum/ACF
use existing estimability rules; within-year panel seasonality is not estimable.
