# Research decisions
- Rich parse_temporal while preserving exact legacy parse_date outputs: existing date consumers assume date key and tests assert dictionaries. A time never receives1900/January defaults.
- Portable locale-independent tokens:%Y,%y,%m,%d,%b,%B,%H,%I,%M,%S,%f,%p,%z,%%. Reject unsupported/modifier tokens and incomplete date/12h patterns with named faults. Alternative platform strptime heuristics rejected for Windows/browser parity.
- Count intraday by written local clock separately for naive and each literal UTC offset. No cross-offset earliest/latest instant, no implicit UTC conversion. Homogeneous declared series may retain explicit offset; mixed bases are declined with evidence.
- configure.build_schema/render_page are shared by Liftoff. Use existing stored samples, not three examples or newly scanned raw values. Preview is sample-only; truncated/unavailable samples disclosed. Native labelled canonical input prevents stale duplicated controls.
- JS pure functions live in YAML_JS too because Node YAML parity tests extract that script without UI_JS. Live preview uses same token contract, no browser locale/Date.parse.
