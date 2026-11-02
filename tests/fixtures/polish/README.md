# Polish review fixtures

movies.csv is the public Vega movies table; headers replace underscores with
spaces and JSON null becomes an empty CSV cell. college.csv is FiveThirtyEight's
public recent-graduates table with only quoting/LF normalization. All rows/columns
are retained. Pinned source URLs, SHA256s, dimensions and exact conversion notes
are in sources.json. Upstream datasets retain their upstream terms:
https://github.com/vega/vega-datasets and https://github.com/fivethirtyeight/data.
These are public review inputs, not independent acceptance tables.

planted.csv and clean.csv are authored synthetic20x7 tables, added after the
implementation commit for a builder acceptance check. Planted: one repeated title,
three zero grosses plus a million-scale tail, one ambiguous two-digit-year date,
one malformed email, four jointly missing rows, and one category typo (Grop A).
Clean: distinct titles, ordinary positive amounts, strict ISO dates, syntactically
valid example.org emails, complete rows and two categories. Deterministic linear
columns deliberately retain benign lockstep structure. See spec006 validation for
found/missed consequences; these are not owner-held unseen acceptance tables.
