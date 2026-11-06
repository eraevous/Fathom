# Commands
Profile YAML:columns.year:{type:temporal,date_format:YEAR}; optional
time_series:[{time:year,value:value,granularities:[year]}].
Panel YAML:series:[entity,candidate],time:year,value:value,period:year,date_format:YEAR.
One observation per declared composite key/year; duplicates fail, never collapse.
Missing years remain absent. Use ISO inclusive bounds for optional window files.
All-failed temporal declarations produce an actionable stderr warning, saved report
finding and exclusion reason. Suggestions never change the declared type/format.
