# Liftoff fixtures

planted.csv: fixed60hours plus one repeated start; one equal interval; cashgroup
31finite zeros versus30nonzero card values. clean.csv: no temporal candidates,
no zeros. periodic.csv:240hours,3+round(2sin(2πhour/24))events/hour, no zero-length
interval; fixed dates, no RNG. constant.csv:120hourly events, undefined ACF under
zero variance. Threshold/denominator/hostile-name cases are additionally authored
in tests/test_liftoff.py.

taxis.csv: public seaborn-data table,6433×14. Exact pinned URL/sha256 in sources.json;
pinned bytes verified against the downloaded file. No private/held-out table used.
