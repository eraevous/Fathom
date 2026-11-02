# Polish review fixtures

movies.csv is the public Vega movies table; headers replace underscores with
spaces and JSON null becomes an empty CSV cell. college.csv is FiveThirtyEight's
public recent-graduates table with only quoting/LF normalization. All rows/columns
are retained. Pinned source URLs, SHA256s, dimensions and exact conversion notes
are in sources.json. Upstream datasets retain their upstream terms:
https://github.com/vega/vega-datasets and https://github.com/fivethirtyeight/data.
These are public review inputs, not independent acceptance tables.
