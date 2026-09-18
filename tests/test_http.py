import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from internet_speed_meter.http import HttpDownloader

PAYLOAD = b"x" * 150_000


class PayloadHandler(BaseHTTPRequestHandler):
    request_count = 0

    def do_GET(self) -> None:
        type(self).request_count += 1
        self.send_response(200)
        self.send_header("Content-Length", str(len(PAYLOAD)))
        self.end_headers()
        self.wfile.write(PAYLOAD)

    def log_message(self, *_args: object) -> None:
        pass


class HttpDownloaderIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        PayloadHandler.request_count = 0
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), PayloadHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        host, port = cls.server.server_address
        cls.url = f"http://{host}:{port}/large-image.jpg"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_counts_bytes_read_in_chunks(self) -> None:
        result = HttpDownloader().download(
            self.url,
            timeout_seconds=2,
            chunk_size=4_096,
        )

        self.assertEqual(result.downloaded_bytes, len(PAYLOAD))
        self.assertGreater(result.elapsed_seconds, 0)
