import io
import unittest

from internet_speed_meter.cli import main
from internet_speed_meter.http import TransferResult
from internet_speed_meter.service import SpeedMeter


class FixedDownloader:
    def download(
        self,
        url: str,
        *,
        timeout_seconds: float,
        chunk_size: int,
    ) -> TransferResult:
        return TransferResult(elapsed_seconds=0.25, downloaded_bytes=2_000_000)


class CliTests(unittest.TestCase):
    def test_prints_required_summary(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = main(
            ["https://example.com/image.jpg", "--requests", "2"],
            stdout=stdout,
            stderr=stderr,
            speed_meter=SpeedMeter(FixedDownloader()),
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn("Среднее время запроса: 0.250 с", stdout.getvalue())
        self.assertIn("Скачано данных:        4.000 МБ", stdout.getvalue())
        self.assertIn("Средняя скорость:      8.000 МБ/с", stdout.getvalue())
