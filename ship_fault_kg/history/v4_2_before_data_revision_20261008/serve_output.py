"""Loopback-only server for Neo4j Browser guides and the local viewer."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).resolve().parent / 'output'), **kwargs)

    def end_headers(self):
        # Public report-derived graph only; do not serve parent folders/passwords.
        self.send_header('Access-Control-Allow-Origin', 'http://localhost:7475')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()


if __name__ == '__main__':
    print('Viewer: http://localhost:8766/graph_viewer.html', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8766), Handler).serve_forever()
