import contextlib
import io
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import speed_meter


PAYLOAD = b"x" * 150_000


class PayloadHandler(BaseHTTPRequestHandler):
    request_count = 0

    def do_GET(self):
        type(self).request_count += 1
        self.send_response(200)
        self.send_header("Content-Length", str(len(PAYLOAD)))
        self.end_headers()
        self.wfile.write(PAYLOAD)

    def log_message(self, *_args):
        pass


class SpeedMeterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        PayloadHandler.request_count = 0
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), PayloadHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        host, port = cls.server.server_address
        cls.url = f"http://{host}:{port}/large-image.jpg"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_measure_downloads_every_response_completely(self):
        before = PayloadHandler.request_count
        messages = []
        results = speed_meter.measure(self.url, 3, 2, output=messages.append)

        self.assertEqual(PayloadHandler.request_count - before, 3)
        self.assertEqual([result.downloaded_bytes for result in results], [len(PAYLOAD)] * 3)
        self.assertEqual(len(messages), 3)

    def test_main_prints_summary(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = speed_meter.main([self.url, "--requests", "2"])

        self.assertEqual(exit_code, 0)
        self.assertIn("Среднее время запроса", output.getvalue())
        self.assertIn("Скачано данных", output.getvalue())
        self.assertIn("Средняя скорость", output.getvalue())

    def test_url_must_use_http_or_https(self):
        with self.assertRaises(Exception):
            speed_meter.validate_url("file:///tmp/picture.jpg")


if __name__ == "__main__":
    unittest.main()
