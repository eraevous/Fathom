"""Authored key/report/control outputs plus existing synthetic panel series."""
from pathlib import Path
from fathom.cli import main
assert main(['profile','tests/fixtures/identifiers/keys.csv','--config','tests/fixtures/identifiers/config.yaml','--out','/tmp/id23-profile'])==0
assert main(['configure','tests/fixtures/identifiers/keys.csv','--out','/tmp/id23-configure'])==0
assert main(['panel','tests/fixtures/panel/panel.csv','--config','tests/fixtures/panel/joined.yaml','--out','/tmp/id23-panel'])==0
