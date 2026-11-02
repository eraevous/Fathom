# Excerpts from Zach's earlier Data Guide design notes (December 2024)

**What these are:** generic passages copied from Zach's own design notes, read with his permission on 2026-11-01. Client-specific material is left out. They are earlier thinking, **not decisions**: they inform `FT-R14`, whose detail is provisional until Zach accepts it. The scope itself, "more advanced univariate analyses and visuals", was accepted in `DG-D5`.

## Numeric columns
> "Count and percentage of zero and negative values."
> "Count of integers vs. non-integers."
> "Percentiles (e.g., 5th, 33rd, 66th, 95th)."
> "Skewness and kurtosis (with simple interpretations)."
> "Most and least common numeric values."
> "Identify invalid or placeholder patterns (e.g., 99999, test, TBD)."

## String and categorical columns
> "Count of blanks (e.g., NA, NaN, empty strings)."
> "Longest and shortest string lengths."
> "Most and least common strings (with counts)."
> "Calculate Shannon entropy to measure diversity in categorical values."
> "Compute the percentage of records covered by the top N categories."

From the analysis checklist:
- all uppercase or all lowercase;
- string length max, min, mean and median;
- sparse category analysis;
- the most common substrings;
- the frequency of special characters.

## Temporal columns
> "Earliest and latest timestamps." "Time span covered by the data." "Temporal gaps between records." "Trends (e.g., record counts by time intervals)."

From the analysis checklist:
- breakdowns by day of week, month, quarter and year;
- autocorrelation;
- outliers in temporal gaps;
- "invalid or inconsistent dates (e.g., `1900-01-01` placeholders)".

## Visuals
> "Bar charts for categorical data." "Histograms and density plots for numeric data."
> "Visualizations are more important to me to add in."

## Scope
> "By focusing on univariate and dataset-level analyses, the module remains manageable while covering essential insights. Delaying multivariate analysis avoids over-engineering and scope creep."
