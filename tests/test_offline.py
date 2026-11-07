"""The privacy contract covers command startup, optional exporters and generated assets."""
import os
import ast
from pathlib import Path
import shutil
import subprocess
import sys
from html.parser import HTMLParser

import pytest

ROOT = Path(__file__).parents[1]
RUNNER = ROOT / 'tests/offline_runner.py'


def invoke(args, blocked=False, seed='19'):
    env = {**os.environ, 'PYTHONPATH': str(ROOT / 'src'),
           'FATHOM_DENY_NETWORK': '1' if blocked else '0', 'PYTHONHASHSEED': seed}
    return subprocess.run([sys.executable, str(RUNNER), *map(str, args)], env=env, capture_output=True)


def test_socket_denial_positive_control():
    r = invoke(['--probe'], True)
    assert r.returncode != 0 and b'offline harness denied socket.__new__' in r.stderr


def test_swallowed_network_error_still_fails_the_offline_harness():
    r = invoke(['--probe-caught'], True)
    assert r.returncode != 0 and b'recorded attempted networking' in r.stderr


def test_application_network_imports_are_denied_with_serializer_exception_scoped():
    r = invoke(['--probe-import'], True)
    assert r.returncode != 0 and b'offline harness denied import urllib.request' in r.stderr
    forbidden = ('requests', 'http', 'urllib.request', 'ftplib', 'smtplib', 'httpx', 'socket', 'socketserver', 'aiohttp', 'websocket', 'websockets')
    for path in (ROOT / 'src/fathom').glob('*.py'):
        for node in ast.walk(ast.parse(path.read_text())):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ''] if isinstance(node, ast.ImportFrom) else []
            if path.name == 'serve.py':
                names = [n for n in names if n not in {'http.server', 'socketserver'}]
            assert not any(n == f or n.startswith(f + '.') for n in names for f in forbidden), path


@pytest.mark.parametrize('command', ['profile', 'render', 'compare', 'validate', 'export', 'configure', 'liftoff', 'panel'])
def test_all_commands_are_socket_free_and_byte_identical(tmp_path, command):
    data = tmp_path / 'data.csv'
    data.write_text('series,time,value\na,2020-01-01,0\na,2020-01-02,2\na,2020-01-03,1\n')
    cfg = tmp_path / 'panel.yaml'
    cfg.write_text('series: [series]\ntime: time\nvalue: value\nperiod: day\n')
    assert invoke(['profile', data, '--out', tmp_path / 'base']).returncode == 0
    artifact = tmp_path / 'base/guide-profile.json'
    out = tmp_path / 'out'
    args = {'render': ['render', artifact], 'compare': ['compare', artifact, artifact],
            'export': ['export', artifact], 'panel': ['panel', data, '--config', cfg]}.get(command, [command, data])
    if command != 'validate': args += ['--out', out]
    first = invoke(args)
    assert first.returncode == 0, first.stderr.decode()
    contents = {str(p.relative_to(out)): p.read_bytes() for p in out.rglob('*') if p.is_file()} if out.exists() else {}
    if out.exists(): shutil.rmtree(out)
    second = invoke(args, True)
    assert second.returncode == 0, second.stderr.decode()
    assert (first.stdout, first.stderr) == (second.stdout, second.stderr)
    assert contents == ({str(p.relative_to(out)): p.read_bytes() for p in out.rglob('*') if p.is_file()} if out.exists() else {})


class Resources(HTMLParser):
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in {'src', 'srcset', 'poster', 'action'} or tag == 'link' and key == 'href':
                assert not value or value.startswith(('data:', '#')), (tag, key, value)


@pytest.mark.parametrize('command,filename', [('profile', 'report.html'), ('configure', 'configure.html'), ('liftoff', 'liftoff.html')])
def test_html_has_no_external_resources(tmp_path, command, filename):
    data = tmp_path / 'x.csv';data.write_text('a,b\n1,x\n2,y\n')
    out = tmp_path / 'out';r = invoke([command, data, '--out', out], True)
    assert r.returncode == 0, r.stderr.decode()
    html = (out / filename).read_text();Resources().feed(html)
    assert all(token not in html.lower() for token in ('@import', 'url(http', 'url(//', 'fetch(', 'xmlhttprequest', 'sendbeacon', 'websocket('))


def test_panel_views_metrics_and_targets_offline_fresh_processes(tmp_path):
    out = tmp_path / 'out'
    args = ['panel', ROOT / 'tests/fixtures/panel/panel.csv', '--config', ROOT / 'tests/fixtures/panel/joined.yaml', '--aggregate', 'week,month', '--out', out]
    a = invoke(args, False, '1');assert a.returncode == 0, a.stderr.decode()
    files = {str(p.relative_to(out)): p.read_bytes() for p in out.rglob('*') if p.is_file()}
    shutil.rmtree(out)
    b = invoke(args, True, '99');assert b.returncode == 0, b.stderr.decode()
    assert (a.stdout, a.stderr) == (b.stdout, b.stderr)
    assert files == {str(p.relative_to(out)): p.read_bytes() for p in out.rglob('*') if p.is_file()}
    assert {'panel.json', 'views/week/panel.json', 'views/month/panel.json', 'targets/0/report.html'} <= files.keys()
    for name, raw in files.items():
        if name.endswith('.html'): Resources().feed(raw.decode())
