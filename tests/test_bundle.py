import json
from pathlib import Path

import pytest

from fathom.bundle import build_bundle, read_manifest, render_index
from fathom.cli import main
from fathom.models import ProfilingResult


def setup_bundle(tmp_path):
    (tmp_path / 'one.csv').write_text('id,value\na,1\nb,\n')
    (tmp_path / 'two.csv').write_text('id,value\na,2\nb,3\n')
    manifest = tmp_path / 'bundle.json'
    manifest.write_text(json.dumps({'version': 1, 'tables': [
        {'id': 'one', 'path': 'one.csv', 'config': {'row_unit': 'observation'}},
        {'id': 'two', 'path': 'two.csv'}]}))
    return manifest


def test_two_tables_deterministic_and_original_profile(tmp_path):
    manifest = setup_bundle(tmp_path)
    first = build_bundle(manifest, tmp_path / 'out1')
    assert [t['status'] for t in first['tables']] == ['ok', 'ok']
    assert first['tables'][0]['row_unit'] == 'observation'
    assert first['tables'][1]['row_unit'] is None
    build_bundle(manifest, tmp_path / 'out2')
    for p in (tmp_path / 'out1').rglob('*'):
        if p.is_file():
            assert p.read_bytes() == (tmp_path / 'out2' / p.relative_to(tmp_path / 'out1')).read_bytes()
    result = ProfilingResult.load(tmp_path / 'out1/one/guide-profile.json')
    assert result.document['source']['origin'] == 'one.csv'
    assert result.document['source']['sha256'] == first['tables'][0]['sha256']
    assert main(['profile', str(tmp_path / 'two.csv'), '--out', str(tmp_path / 'single')]) == 0
    original = ProfilingResult.load(tmp_path / 'single/guide-profile.json').document
    bundled = ProfilingResult.load(tmp_path / 'out1/two/guide-profile.json').document
    original['source']['origin'] = 'two.csv'
    assert original == bundled


@pytest.mark.parametrize('bad', ['missing.csv', '../escape.csv', '/etc/passwd', 'https://example.com/x', 'C:\\x.csv'])
def test_partial_failure_and_no_failed_report(tmp_path, bad):
    manifest = setup_bundle(tmp_path)
    doc = json.loads(manifest.read_text()); doc['tables'][0]['path'] = bad
    manifest.write_text(json.dumps(doc))
    assert main(['bundle', str(manifest), '--out', str(tmp_path / 'out')]) == 2
    index = json.loads((tmp_path / 'out/bundle-index.json').read_text())
    assert [t['status'] for t in index['tables']] == ['error', 'ok']
    assert not (tmp_path / 'out/one').exists()
    assert 'Unavailable' in (tmp_path / 'out/index.html').read_text()


def test_symlink_escape_and_existing_output(tmp_path):
    root = tmp_path / 'root'; root.mkdir()
    manifest = setup_bundle(root)
    (tmp_path / 'outside.csv').write_text('id\na\n')
    (root / 'one.csv').unlink(); (root / 'one.csv').symlink_to(tmp_path / 'outside.csv')
    assert build_bundle(manifest, root / 'out')['tables'][0]['status'] == 'error'
    with pytest.raises(ValueError, match='new directory'):
        build_bundle(manifest, root / 'out')


@pytest.mark.parametrize('raw', [b'{}', b'{"version":1,"tables":[]}',
    b'{"version":true,"tables":[{"id":"x","path":"x"}]}',
    b'{"version":1,"version":1,"tables":[]}',
    b'{"version":1,"tables":[{"id":"../bad","path":"x"}]}',
    b'{"version":1,"tables":[{"id":"x","path":"x"},{"id":"x","path":"y"}]}'])
def test_bad_manifest(raw):
    with pytest.raises(ValueError): read_manifest(raw)


def test_malformed_csv_and_bad_config_are_isolated(tmp_path):
    manifest = setup_bundle(tmp_path)
    (tmp_path / 'one.csv').write_text('id,id\na,b\n')
    assert build_bundle(manifest, tmp_path / 'badcsv')['tables'][0]['status'] == 'error'
    doc = json.loads(manifest.read_text());doc['tables'][1]['config'] = {'row_unit': 123}
    manifest.write_text(json.dumps(doc))
    assert build_bundle(manifest, tmp_path / 'badconfig')['tables'][1]['status'] == 'error'


def test_html_escapes_declarations():
    html = render_index({'tables': [{'id':'x','status':'ok','report':'x/report.html',
                                    'row_unit':'<script>alert(1)</script>'}]})
    assert '<script>' not in html
    assert '&lt;script&gt;' in html


@pytest.mark.parametrize('name', ['con', 'aux', 'nul', 'prn', 'com1', 'lpt9'])
def test_reserved_windows_ids(name):
    with pytest.raises(ValueError, match='reserved'):
        read_manifest(json.dumps({'version': 1, 'tables': [{'id': name, 'path': 'x.csv'}]}).encode())


def test_symlink_output_and_prevalidation_no_writes(tmp_path):
    manifest = setup_bundle(tmp_path)
    output = tmp_path / 'output'; output.symlink_to(tmp_path / 'absent', target_is_directory=True)
    with pytest.raises(ValueError, match='new directory'):
        build_bundle(manifest, output)
    manifest.write_text('{"version":1,"tables":[]}')
    with pytest.raises(ValueError):
        build_bundle(manifest, tmp_path / 'new')
    assert not (tmp_path / 'new').exists()
