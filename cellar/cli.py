import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .pipeline import run

def main():
    parser = argparse.ArgumentParser(description='Cellar battery dispatch research')
    sub = parser.add_subparsers(dest='command', required=True)
    build = sub.add_parser('replay'); build.add_argument('--output', default='reports/custom')
    serve = sub.add_parser('serve'); serve.add_argument('--port', type=int, default=8792)
    args = parser.parse_args(); root = Path.cwd()
    if not (root/'docs/PROTOCOL.md').exists(): parser.error('Run from the repository root')
    if args.command == 'replay': run(root, args.output)
    else:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(SimpleHTTPRequestHandler, directory=str(root)))
        print(f'Cellar preview: http://127.0.0.1:{args.port}/', flush=True)
        try: server.serve_forever()
        except KeyboardInterrupt: pass
        finally: server.server_close()

if __name__ == '__main__': main()
