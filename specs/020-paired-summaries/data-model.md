# Derived model only
No saved-artifact/schema2 modification. A FindingNode has text, child nodes and an
optional exact stored verdict token. A SummaryTable has caption/type, header labels,
rows, numeric columns and dictionary links. Orientation transposes the same cells.
ReportOptions contains summary_orientation only, not persisted. Tidy tables contain
raw scalar values and stable escaped metric/evidence paths. Empty containers/nulls
have documented CSV representations. Nesting metrics count terminal edge depth below
each top-level key; median includes every terminal (empty containers count as leaves).
