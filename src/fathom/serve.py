"""Small authenticated loopback transport for the existing profile/configurator.

No directory handler, requested paths, shell, uploads or network lookups. Imported
only for the explicitly local server command; standalone report files stay static.
"""
from collections import deque
from contextlib import redirect_stdout, redirect_stderr
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
from html import escape
from io import StringIO
import ipaddress
import json
import math
from pathlib import Path
import secrets
import socketserver
import sys
import time
from urllib.parse import parse_qs, urlsplit

from .config import config_from_yaml, read_config, validate_config
from .configure import build_schema, render_page
from .connectors import CSVConnector
from .models import ProfilingResult, SchemaContract

MAX_BODY = 65536
_GUARD_INSTALLED = False
_DENIED = []


def _loopback(host):
    try:
        return ipaddress.ip_address(host).is_loopback
    except (ValueError, TypeError):
        return False


def network_guard(event, args):
    """Process-wide guard: no DNS or socket address beyond numeric loopback."""
    denied = False
    if event in {'socket.connect', 'socket.bind', 'socket.sendto'}:
        address = args[-1]
        denied = not isinstance(address, tuple) or not _loopback(address[0])
    elif event in {'socket.getaddrinfo', 'socket.gethostbyname'}:
        denied = not _loopback(args[0])
    elif event in {'socket.gethostbyaddr', 'socket.getnameinfo', 'urllib.Request'}:
        denied = True
    if denied:
        _DENIED.append(event)
        raise RuntimeError('outbound networking disabled in guide serve')


def install_network_guard():
    global _GUARD_INSTALLED
    if not _GUARD_INSTALLED:
        sys.addaudithook(network_guard)
        _GUARD_INSTALLED = True


class Session:
    """Only startup paths can reach the profiler; request content is config only."""
    def __init__(self, data, out, config=None, *, idle_timeout=1800):
        if not math.isfinite(idle_timeout) or idle_timeout <= 0:
            raise ValueError('idle timeout must be positive and finite')
        self.data = Path(data)
        self.fixed_data = self.data.resolve(strict=True)
        self.out = Path(out).resolve()
        self.idle_timeout = idle_timeout
        self.token = secrets.token_urlsafe(32)
        self.origin = None
        self.stopped = False
        self.last_active = time.monotonic()
        self.events = deque(maxlen=200)
        self.raw = read_config(config) if config else {}
        self.rerun(json_to_yaml(self.raw))

    def check_paths(self):
        if self.data.resolve(strict=True) != self.fixed_data:
            raise ValueError('startup data path changed')
        if self.out.resolve() != self.out:
            raise ValueError("startup output directory changed")
        if not self.out.parent.exists():
            # Resolve/create the chosen directory only at startup; no request paths.
            self.out.parent.mkdir(parents=True, exist_ok=True)
        for name in ('server-config.yaml', 'serve.log', 'report.html', 'report.md', 'guide-profile.json'):
            p = self.out / name
            if p.is_symlink() or (p.exists() and (p.stat().st_nlink != 1 or p.resolve() == self.fixed_data)):
                raise ValueError('unsafe fixed output destination')
        if self.out.exists() and not self.out.is_dir():
            raise ValueError('output must be a directory')

    def log(self, action):
        # Fixed event labels only; no request line, token, config or data in logs.
        self.events.append(action)
        self.check_paths()
        (self.out / 'serve.log').write_text('\n'.join(self.events)+'\n', encoding='utf-8')

    def rerun(self, contents):
        if len(contents.encode('utf-8')) > MAX_BODY:
            raise ValueError('configuration is too large')
        raw = config_from_yaml(contents)
        cfg = validate_config(raw)
        self.check_paths()
        data = CSVConnector(self.data, SchemaContract(**cfg['schema'])).load()
        validate_config(raw, list(data.frame.columns))
        before = len(_DENIED)
        self.out.mkdir(parents=True, exist_ok=True)
        config = self.out / 'server-config.yaml'
        config.write_text(contents, encoding='utf-8', newline='\n')
        from .cli import main
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            code = main(['profile', str(self.data), '--config', str(config), '--out', str(self.out)])
        if code or len(_DENIED) != before:
            raise ValueError('profile failed; review the configuration locally')
        result = ProfilingResult.load(self.out / 'guide-profile.json')
        if result.document['source']['sha256'] != data.source['sha256']:
            raise ValueError('CSV changed during profile; retry with a stable file')
        self.schema = build_schema(result.document, data.frame, raw)
        self.raw = raw
        self.last_active = time.monotonic()
        self.log('profile completed')

    def page(self):
        page = render_page(self.schema)
        url = '/report?token=' + self.token
        toolbar = ('<section id="local-session"><h2>Local rerun session</h2>'
                   '<p>This session uses the startup CSV and output directory only. '
                   'Idle expiry: '+str(self.idle_timeout)+' seconds. Saved reports work after Stop.</p>'
                   '<button id="rerun" type="button" hidden>Rerun with this configuration</button> '
                   '<button id="stop" type="button" hidden>Stop local server</button>'
                   '<p id="session-status" role="status">Ready</p>'
                   '<noscript><p>JavaScript is off: copy YAML and use the profile command below; Stop from the terminal with Ctrl+C.</p></noscript>'
                   '<iframe id="local-report" title="Standalone profile report" sandbox="allow-scripts" '
                   'style="width:100%;height:70vh;border:1px solid currentColor" src="'+escape(url, quote=True)+'"></iframe></section>')
        script = '''<script>
(function(){
const token=TOKEN;
const state=document.getElementById('session-status');
document.getElementById('rerun').hidden=false;document.getElementById('stop').hidden=false;
async function send(route,body){
 const response=await fetch('/'+route+'?token='+token,{method:'POST',headers:{'Content-Type':'application/yaml'},body:body,credentials:'omit',cache:'no-store'});
 if(!response.ok)throw new Error('Request rejected ('+response.status+'). Check the configuration.');
 return response.json();
}
document.getElementById('rerun').onclick=async function(){
 this.disabled=true;state.textContent='Profiling the fixed local CSV…';
 try{const answer=await send('rerun',document.getElementById('yaml').textContent);const frame=document.getElementById('local-report');await new Promise(resolve=>{frame.onload=resolve;frame.src=answer.report;});state.textContent='Report updated';}
 catch(e){state.textContent=e.message;}finally{this.disabled=false;}
};
document.getElementById('stop').onclick=async function(){try{await send('stop','');state.textContent='Stopped. Saved reports remain available on disk.';document.getElementById('rerun').disabled=true;this.disabled=true;}catch(e){state.textContent=e.message;}};
})();</script>'''.replace('TOKEN', json.dumps(self.token))
        # Controls exist only in this ephemeral response, never in saved HTML.
        frame_at = toolbar.index('<iframe')
        controls = toolbar[:frame_at]+'<a href="#live-report">Read updated report</a></section>'
        frame = '<section id="live-report"><h2>Updated standalone report</h2>'+toolbar[frame_at:]
        return page.replace('<p class="legend">', controls+'<p class="legend">', 1).replace('Nothing here changes the data or runs new analysis.', 'Controls edit YAML only; Rerun runs the fixed local profile.').replace('</body>', frame+script+'</body>')


def json_to_yaml(raw):
    import yaml
    return yaml.safe_dump(raw, sort_keys=False, allow_unicode=True)


class LocalServer(HTTPServer):
    def server_bind(self):
        # HTTPServer's default calls getfqdn: avoid reverse lookup entirely.
        socketserver.TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(2)
        return connection, address


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.0'

    def log_message(self, *args):
        pass  # Base handler would leak token-bearing request URLs.

    @property
    def session(self):
        return self.server.session

    def respond(self, status, body, content_type='text/plain; charset=utf-8'):
        if isinstance(body, str): body = body.encode('utf-8')
        self.send_response(status)
        for name, value in {
            'Content-Type': content_type, 'Content-Length': str(len(body)),
            'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
            'Referrer-Policy': 'no-referrer', 'Connection': 'close',
            'Content-Security-Policy': "default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src data:; connect-src 'self'; frame-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'self'",
        }.items(): self.send_header(name, value)
        self.end_headers()
        if self.command != 'HEAD': self.wfile.write(body)
        self.close_connection = True

    def send_error(self, code, message=None, explain=None):
        self.respond(code, 'Request rejected')

    def parse_request(self):
        if not super().parse_request(): return False
        s = self.session
        host = self.headers.get_all('Host', [])
        origins = self.headers.get_all('Origin', [])
        if host != [s.origin.removeprefix('http://')] or len(origins) > 1 or (origins and origins != [s.origin]) or (self.command == 'POST' and origins != [s.origin]):
            self.respond(403, 'Host/Origin rejected'); return False
        try:
            u = urlsplit(self.path)
            params = parse_qs(u.query, keep_blank_values=True, strict_parsing=True)
            token = params.get('token', [])
            valid = (self.path.startswith('/') and not self.path.startswith('//') and not u.scheme and not u.netloc and not u.fragment and set(params) == {'token'} and len(token) == 1 and hmac.compare_digest(token[0], s.token))
        except (ValueError, TypeError): valid = False
        if not valid:
            self.respond(403, 'Session token rejected'); return False
        self.route = u.path
        s.last_active = time.monotonic()
        return True

    def do_GET(self):
        if self.route == '/':
            self.respond(200, self.session.page(), 'text/html; charset=utf-8')
        elif self.route == '/report':
            self.session.check_paths()
            self.respond(200, (self.session.out / 'report.html').read_bytes(), 'text/html; charset=utf-8')
        else: self.respond(404, 'Unknown resource')

    def do_POST(self):
        if self.route not in {'/rerun', '/stop'}:
            self.respond(404, 'Unknown resource'); return
        lengths = self.headers.get_all('Content-Length', [])
        if self.headers.get_all('Transfer-Encoding', []) or len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdigit():
            self.respond(400, 'A single bounded Content-Length is required'); return
        if len(lengths[0]) > 8:
            self.respond(413, 'Body too large'); return
        size = int(lengths[0])
        if size > MAX_BODY or (self.route == '/stop' and size):
            self.respond(413, 'Body too large'); return
        types = self.headers.get_all('Content-Type', [])
        if len(types) != 1 or types[0].split(';')[0].strip() not in {'application/yaml', 'text/yaml'}:
            self.respond(415, 'YAML only'); return
        try:
            body = self.rfile.read(size)
            if len(body) != size: raise ValueError('Incomplete body')
            if self.route == '/stop':
                self.session.stopped = True
                self.session.log('stop requested')
                answer = {'stopped': True}
            else:
                self.session.rerun(body.decode('utf-8'))
                answer = {'report': '/report?token='+self.session.token}
            self.respond(200, json.dumps(answer), 'application/json')
        except (ValueError, OSError, RuntimeError, RecursionError) as error:
            # Error details may contain a hostile YAML payload: do not echo/log it.
            self.respond(400, 'Configuration rejected; use guide validate locally for details')
        except Exception as error:
            import yaml
            if isinstance(error, yaml.YAMLError):
                self.respond(400, 'Invalid YAML')
            else: raise


def create_server(data, out, config=None, *, host='127.0.0.1', idle_timeout=1800):
    if host != '127.0.0.1': raise ValueError('serve binds only 127.0.0.1')
    install_network_guard()
    session = Session(data, out, config, idle_timeout=idle_timeout)
    server = LocalServer((host, 0), Handler)
    server.session = session
    session.origin = 'http://127.0.0.1:'+str(server.server_port)
    server.timeout = min(.2, idle_timeout)
    return server


def run(data, out, config=None, *, host='127.0.0.1', idle_timeout=1800):
    server = create_server(data, out, config, host=host, idle_timeout=idle_timeout)
    s = server.session
    print(s.origin+'/?token='+s.token, flush=True)
    print('guide: local fixed-file session; Ctrl+C or Stop; idle '+str(idle_timeout)+'s; log '+str(s.out/'serve.log'), flush=True)
    try:
        while not s.stopped and time.monotonic()-s.last_active < s.idle_timeout:
            server.handle_request()
        s.log('session closed')
    except KeyboardInterrupt:
        s.log('terminal stop')
    finally:
        server.server_close()
    return 0
