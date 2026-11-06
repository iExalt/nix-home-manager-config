"""Serves the app with a backend that answers detail requests after a random delay, like production."""
import functools
import http.server
import os
import random
import threading
import time

import pytest

ROOT = os.path.dirname(os.path.abspath(__file__))
DELAY_MS = tuple(int(v) for v in os.environ.get("DETAILS_DELAY_MS", "100-600").split("-"))


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/details/"):
            time.sleep(random.uniform(*DELAY_MS) / 1000)
        super().do_GET()

    def log_message(self, *args):
        pass


@pytest.fixture(scope="session")
def app_url():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=ROOT))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}/index.html"
    server.shutdown()
