"""Serve the local TH06nc game and diagnostics with explicit ES module MIME types."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class Handler(SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, '.mjs':'text/javascript', '.js':'text/javascript', '.wasm':'application/wasm'}


class PreviewServer(ThreadingHTTPServer):
    # The browser loads the shared ES-module graph before GameAssets' bounded
    # fetch queue exists. Windows' small default listen backlog can reject it.
    request_queue_size = 128


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8268)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    server=PreviewServer(('127.0.0.1',args.port),partial(Handler,directory=str(root)))
    print(f'http://127.0.0.1:{args.port}/runtimes/th06nc/game.html',flush=True)
    server.serve_forever()
