"""Fresh-process offline harness; denies sockets before importing any application code."""
import importlib.abc
import os
import sys

attempts = []

if os.environ.get('FATHOM_DENY_NETWORK') == '1':
    def deny(event, args):
        if event.startswith(('socket.', 'urllib.Request')):
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
                    if str(frame.f_globals.get('__name__', '')).startswith(('reportlab.', 'pptx.')):
                        return None
                    frame = frame.f_back
                attempts.append('import ' + fullname)
                raise RuntimeError('offline harness denied import ' + fullname)
    sys.meta_path.insert(0, NoNetworkClients())

if __name__ == '__main__':
    if sys.argv[1:] == ['--probe']:
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
