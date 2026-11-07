"""Fresh-process offline harness; denies sockets before importing any application code."""
import importlib.abc
import os
import sys

attempts = []
loopback = os.environ.get("FATHOM_ALLOW_LOOPBACK") == "1"

def allowed_loopback(event, args):
    if not loopback: return False
    import ipaddress
    if event == "socket.__new__": return True
    if event in {"socket.connect", "socket.bind", "socket.sendto"}:
        address = args[-1]
        host = address[0] if isinstance(address, tuple) else None
    elif event in {"socket.getaddrinfo", "socket.gethostbyname"}: host = args[0]
    else: return False
    try: return ipaddress.ip_address(host).is_loopback
    except (ValueError, TypeError): return False


if os.environ.get('FATHOM_DENY_NETWORK') == '1':
    def deny(event, args):
        if event.startswith(('socket.', 'urllib.Request')) and not allowed_loopback(event, args):
            attempts.append(event)
            raise RuntimeError('offline harness denied ' + event)
    sys.addaudithook(deny)

    class NoNetworkClients(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if any(fullname == p or fullname.startswith(p + '.') for p in
                   ('requests', 'http.client', 'urllib.request', 'ftplib', 'smtplib', 'httpx')):
                # Existing optional serializers import unused stdlib URL helpers.
                # Socket/Request auditing still denies every attempted connection.
                frame = sys._getframe()
                while frame:
                    if (str(frame.f_globals.get('__name__', '')).startswith(('reportlab.', 'pptx.'))
                        or (loopback and fullname == 'http.client' and frame.f_globals.get('__name__') == 'http.server')):
                        return None
                    frame = frame.f_back
                attempts.append('import ' + fullname)
                raise RuntimeError('offline harness denied import ' + fullname)
    sys.meta_path.insert(0, NoNetworkClients())

if __name__ == '__main__':
    if sys.argv[1:] == ['--probe-external']:
        import socket
        socket.socket().connect(('192.0.2.1', 80))
        code = 0
    elif sys.argv[1:] == ['--probe']:
        import socket
        socket.socket()
        code = 0
    elif sys.argv[1:] == ['--probe-import']:
        __import__('urllib.request')
        code = 0
    elif sys.argv[1:] == ['--probe-caught']:
        try:
            import socket
            socket.socket()
        except RuntimeError:
            pass
        code = 0
    else:
        from fathom.cli import main
        code = main(sys.argv[1:])
    if attempts:
        raise RuntimeError('offline harness recorded attempted networking: ' + repr(attempts))
    raise SystemExit(code)
