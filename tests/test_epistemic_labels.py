"""Label completeness and the exact, append-only DEC-095 authorization boundary."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def read_records(raw):
    return [json.loads(line) for line in raw.splitlines() if line.strip() and not line.startswith('//')]


def test_latest_records_have_explicit_epistemic_labels():
    latest = {r['id']: r for r in read_records((ROOT / '.aec/records.jsonl').read_text())}
    assert all(r.get('epistemic') in {'committed', 'provisional'} for r in latest.values())


def test_depth_migration_changes_only_version_and_label():
    audit = json.loads((ROOT / 'docs/telosmith-adoption/labels.json').read_text())
    raw = (ROOT / '.aec/records.jsonl').read_bytes()
    prefix = raw[:audit['prefix_bytes']]
    assert hashlib.sha256(prefix).hexdigest() == audit['prefix_sha256']
    original = {r['id']: r for r in read_records(prefix.decode())}
    appended = read_records(raw[audit['prefix_bytes']:].decode())[:len(audit['records'])]
    assert len(appended) == len(audit['records']) == 61
    assert {r['id'] for r in appended} == {k for k, v in original.items() if 'epistemic' not in v}
    for current, entry in zip(appended, audit['records']):
        previous = original[current['id']]
        assert entry['from'] == current['id'] + '@' + str(previous['version'])
        assert entry['to'] == current['id'] + '@' + str(current['version'])
        assert current['version'] == previous['version'] + 1
        assert {k: v for k, v in current.items() if k not in {'version', 'epistemic'}} == {k: v for k, v in previous.items() if k != 'version'}
        assert current['epistemic'] == entry['epistemic']
        if current['epistemic'] == 'committed':
            assert previous['type'] == 'decision' and previous['status'] == 'accepted'
            assert all(c['quote'] in (ROOT / c['path']).read_text() for c in entry['citations'])
        else:
            assert entry['reason'] and not entry.get('citations')

