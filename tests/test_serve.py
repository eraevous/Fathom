"""Real authenticated HTTP sessions under an independent outbound-denial harness."""
from contextlib import contextmanager
import http.client
import json
import os
from pathlib import Path
import re
import select
import socket
import subprocess
import sys
import time
from urllib.parse import urlsplit

import pytest

ROOT = Path(__file__).parents[1]
ENV = {**os.environ, 'PYTHONPATH': str(ROOT/'src'), 'FATHOM_DENY_NETWORK':'1', 'FATHOM_ALLOW_LOOPBACK':'1'}


@contextmanager
def running(tmp_path, timeout=15):
    data = tmp_path/'synthetic.csv'
    data.write_text('key,value,group\na,0,x\nb,2,y\nc,9,x\nd,,y\n')
    out = tmp_path/'out'
    p = subprocess.Popen([sys.executable, '-u', str(ROOT/'tests/offline_runner.py'), 'serve', str(data), '--out', str(out), '--idle-timeout', str(timeout)], env=ENV, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    ready = select.select([p.stdout], [], [], 15)[0]
    assert ready, 'server startup timed out'
    url = p.stdout.readline().strip()
    if not url.startswith('http://127.0.0.1:'):
        p.terminate(); stdout, stderr = p.communicate(timeout=5)
        pytest.fail('server did not start: '+stderr)
    u=urlsplit(url)
    client = Client(u.netloc, u.query, p, out, data)
    try: yield client
    finally:
        if p.poll() is None:
            try: client.request('POST', '/stop', b'')
            except OSError: p.terminate()
        stdout, stderr = p.communicate(timeout=8)
        assert p.returncode == 0, stderr
        assert 'recorded attempted networking' not in stderr


class Client:
    def __init__(self, host, query, process, out, data):
        self.host,self.query,self.process,self.out,self.data=host,query,process,out,data
        self.origin='http://'+host

    def request(self, method='GET', path='/', body=None, *, token=True, headers=None):
        conn=http.client.HTTPConnection(self.host, timeout=10)
        h={'Host':self.host}
        if method=='POST': h.update({'Origin':self.origin,'Content-Type':'application/yaml'})
        if headers is not None: h.update(headers)
        path=path+('?' + self.query if token else '')
        conn.request(method,path,body=body,headers=h)
        response=conn.getresponse(); answer=(response.status,dict(response.getheaders()),response.read());conn.close()
        return answer

    def files(self):
        return {name:(self.out/name).read_bytes() for name in ('report.html','report.md','guide-profile.json')}


@pytest.mark.parametrize('host',['0.0.0.0','localhost','::1','192.0.2.1'])
def test_nonloopback_bind_refused_before_output(tmp_path,host):
    r=subprocess.run([sys.executable,str(ROOT/'tests/offline_runner.py'),'serve','absent.csv','--out',str(tmp_path/'no'),'--host',host],env=ENV,capture_output=True)
    assert r.returncode!=0 and not (tmp_path/'no').exists()


@pytest.mark.parametrize('timeout',['0','-1','nan','inf'])
def test_invalid_timeout_refused(tmp_path,timeout):
    data=tmp_path/'d.csv';data.write_text('a\n1\n')
    r=subprocess.run([sys.executable,str(ROOT/'tests/offline_runner.py'),'serve',str(data),'--out',str(tmp_path/'no'),'--idle-timeout',timeout],env=ENV,capture_output=True)
    assert r.returncode!=0 and not (tmp_path/'no').exists()


def test_every_request_needs_token_and_exact_authority(tmp_path):
    with running(tmp_path) as c:
        before=c.files()
        for method,path in [('GET','/'),('GET','/report'),('POST','/rerun'),('POST','/stop'),('HEAD','/'),('OPTIONS','/'),('PUT','/')]:
            assert c.request(method,path,b'' if method=='POST' else None,token=False)[0]==403
        good=c.query;c.query='token=wrong'
        assert c.request()[0]==403
        c.query=good+'&'+good;assert c.request()[0]==403
        c.query=good
        for headers in [{'Host':'localhost:'+c.host.split(':')[1]}, {'Host':'evil.example'}, {'Origin':'null'}, {'Origin':'https://evil.example'}, {'Host':''}]:
            assert c.request(headers=headers)[0]==403
        assert c.request('POST','/rerun',b'{}\n',headers={'Origin':''})[0]==403
        status,h,body=c.request();assert status==200
        assert all(k in h for k in ('Cache-Control','Referrer-Policy','X-Content-Type-Options','Content-Security-Policy'))
        assert c.files()==before
        status, h, _ = c.request('OPTIONS')
        assert status == 501 and h['Cache-Control'] == 'no-store'


@pytest.mark.parametrize('payload',[
    b'input: /etc/passwd\n',b'out: /tmp/escape\n',b'command: whoami\n',
    b'pair_budget: 1\npair_budget: 2\n',b'!!python/object/apply:os.system [whoami]',
    b'columns: {absent: {type: numeric}}',b'[invalid',b'\xff',b'columns: {value: {type: fictional}}',
])
def test_hostile_config_and_clean_decoy(tmp_path,payload):
    with running(tmp_path) as c:
        before=c.files();source=c.data.read_bytes()
        assert c.request('POST','/rerun',payload)[0]==400
        assert c.files()==before and c.data.read_bytes()==source
        assert c.request('POST','/rerun',b'pair_budget: 0\n')[0]==200


def test_routes_body_bounds_and_output_symlink(tmp_path):
    with running(tmp_path) as c:
        before=c.files()
        for route in ['/../synthetic.csv','/%2e%2e/synthetic.csv','/synthetic.csv','/etc/passwd','/uploads']:
            assert c.request(path=route)[0]==404
        assert c.request('POST','/rerun',b'{}',headers={'Content-Type':'application/json'})[0]==415
        assert c.request('POST','/rerun',b'{}',headers={'Content-Type':'multipart/form-data'})[0]==415
        assert c.request('POST','/rerun',b'{}',headers={'Content-Length':'65537'})[0]==413
        assert c.request('POST','/rerun',b'{}',headers={'Content-Length':'-1'})[0]==400
        assert c.request('POST','/rerun',b'{}',headers={'Transfer-Encoding':'chunked'})[0]==400
        assert c.files()==before
        victim=tmp_path/'victim';victim.write_text('untouched')
        report=c.out/'report.md';report.unlink();report.symlink_to(victim)
        assert c.request('POST','/rerun',b'{}')[0]==400
        assert victim.read_text()=='untouched'
        report.unlink();report.write_bytes(before['report.md'])


def test_rerun_is_cli_byte_identical_and_static_report(tmp_path):
    with running(tmp_path) as c:
        yaml=b'title: Synthetic checks\npair_budget: 0\n'
        assert c.request('POST','/rerun',yaml)[0]==200
        first=c.files();assert c.request('POST','/rerun',yaml)[0]==200
        assert c.files()==first
        cli=tmp_path/'ordinary'
        r=subprocess.run([sys.executable,str(ROOT/'tests/offline_runner.py'),'profile',str(c.data),'--out',str(cli),'--config',str(c.out/'server-config.yaml')],env={**ENV,'FATHOM_ALLOW_LOOPBACK':'0'},capture_output=True)
        assert r.returncode==0,r.stderr.decode()
        assert first=={name:(cli/name).read_bytes() for name in first}
        assert c.request(path='/report')[2]==first['report.html']
        assert b'Rerun with this configuration' not in first['report.html']
        page=c.request()[2];assert b'id="rerun"' in page and b'guide profile DATA.csv' in page
        log=(c.out/'serve.log').read_text();assert 'Synthetic checks' not in log and c.query not in log


def test_session_tokens_random_port_zero_and_stop(tmp_path):
    a=tmp_path/'a';b=tmp_path/'b';a.mkdir();b.mkdir()
    with running(a) as x, running(b) as y:
        assert x.query!=y.query and x.host!=y.host
        assert x.host.startswith('127.0.0.1:')
        assert x.request('POST','/stop',b'')[0]==200
        x.process.wait(timeout=5)
        with pytest.raises(OSError):x.request()


def test_idle_timeout_and_unauthenticated_requests_do_not_refresh(tmp_path):
    with running(tmp_path,timeout=.6) as c:
        for _ in range(3):
            assert c.request(token=False)[0]==403
            time.sleep(.12)
        c.process.wait(timeout=4)
        assert c.process.returncode==0


def test_nonloopback_positive_controls_are_blocked_without_packet():
    r=subprocess.run([sys.executable,str(ROOT/'tests/offline_runner.py'),'--probe-external'],env=ENV,capture_output=True)
    assert r.returncode!=0 and b'offline harness denied socket.connect' in r.stderr
    script="from fathom.serve import install_network_guard; install_network_guard(); import socket; socket.socket().connect(('192.0.2.1',80))"
    r=subprocess.run([sys.executable,'-c',script],env=ENV,capture_output=True)
    assert r.returncode!=0 and b'outbound networking disabled' in r.stderr


def test_duplicate_headers_rejected(tmp_path):
    with running(tmp_path) as c:
        for duplicate in ['Host: '+c.host,'Origin: '+c.origin]:
            request=(f'POST /rerun?{c.query} HTTP/1.0\r\nHost: {c.host}\r\nOrigin: {c.origin}\r\n{duplicate}\r\nContent-Length: 2\r\nContent-Type: application/yaml\r\n\r\n{{}}').encode()
            host,port=c.host.split(':')
            with socket.create_connection((host,int(port))) as sock:
                sock.sendall(request);answer=sock.recv(4096)
            assert b' 403 ' in answer


def test_fixed_profile_path_default_timeout_and_bounded_log(tmp_path,monkeypatch):
    from fathom.serve import Session
    from fathom import cli
    data=tmp_path/'d.csv';data.write_text('key,value\na,1\nb,2\n')
    calls=[];ordinary=cli.main
    def observed(args):
        calls.append(args)
        return ordinary(args)
    monkeypatch.setattr(cli,'main',observed)
    s=Session(data,tmp_path/'out')
    s.rerun('pair_budget: 0\n')
    assert s.idle_timeout==1800
    assert len(calls)==2 and all(a[0:2]==['profile',str(data)] for a in calls)
    assert all(a[-1]==str(s.out) for a in calls)
    for _ in range(210):s.log('profile completed')
    assert len((s.out/'serve.log').read_text().splitlines())==200
    assert s.token not in (s.out/'serve.log').read_text()


@pytest.mark.parametrize('kind',['hardlink','source_collision','directory_swap'])
def test_output_escape_and_source_collision_refused(tmp_path,kind):
    from fathom.serve import Session
    data=tmp_path/'d.csv';data.write_text('a\n1\n2\n')
    out=tmp_path/'out';s=Session(data,out)
    victim=tmp_path/'victim';victim.write_text('untouched')
    if kind=='hardlink':
        (out/'report.md').unlink();os.link(victim,out/'report.md')
    elif kind=='source_collision':
        s.data=out/'report.md';s.fixed_data=s.data.resolve()
    else:
        out.rename(tmp_path/'original');out.symlink_to(tmp_path/'outside',target_is_directory=True)
    with pytest.raises(ValueError):s.rerun('{}\n')
    assert victim.read_text()=='untouched'
    assert not (tmp_path/'outside').exists()
