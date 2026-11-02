# Additive artifact model

GuideDataFrame.raw_rows optionally stores original lexical CSV rows; frame keeps
canonical missing-value policy. dataset identity has title/description text,
generator/status and basis. samples has size/seed/text_limit/columns, raw-values
note, first/last/random lists of {position (1-based), values, truncated_cells}.

Each column.univariate has statistics, bounded chart specs and parse/role basis.
Charts contain kind/title/x_label/y_label plus bins/counts/box values. All numbers
are finite or null. Date parse evidence includes formats, ambiguities, two-digit
counts and canonical date examples; original values remain in dictionary/samples.
Validate optional fields; legacy artifact fields remain valid without them.
