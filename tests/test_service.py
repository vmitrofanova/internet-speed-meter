import unittest

from internet_speed_meter.config import MeasurementConfig
from internet_speed_meter.http import DownloadError, TransferResult
from internet_speed_meter.service import MeasurementError, SpeedMeter


class FakeDownloader:
    def __init__(self, *, fail_on_call: int | None = None) -> None:
        self.calls: list[str] = []
        self.fail_on_call = fail_on_call

    def download(
        self,
        url: str,
        *,
        timeout_seconds: float,
        chunk_size: int,
    ) -> TransferResult:
        self.calls.append(url)
        if len(self.calls) == self.fail_on_call:
            raise DownloadError("network unavailable")
        return TransferResult(elapsed_seconds=0.5, downloaded_bytes=1_000_000)


class SpeedMeterTests(unittest.TestCase):
    def test_runs_ten_requests_sequentially_by_default(self) -> None:
        downloader = FakeDownloader()
        observed_sequences: list[int] = []

        report = SpeedMeter(downloader).run(
            MeasurementConfig("https://example.com/image.jpg"),
            on_progress=lambda sample, _count: observed_sequences.append(
                sample.sequence_number
            ),
        )

        self.assertEqual(len(downloader.calls), 10)
        self.assertEqual(observed_sequences, list(range(1, 11)))
        self.assertEqual(report.request_count, 10)
        self.assertEqual(report.total_bytes, 10_000_000)

    def test_aborts_without_publishing_partial_report_on_failure(self) -> None:
        downloader = FakeDownloader(fail_on_call=3)

        with self.assertRaisesRegex(MeasurementError, "запрос 3/10"):
            SpeedMeter(downloader).run(
                MeasurementConfig("https://example.com/image.jpg")
            )

        self.assertEqual(len(downloader.calls), 3)

    def test_configuration_rejects_unsupported_url(self) -> None:
        with self.assertRaisesRegex(ValueError, "HTTP"):
            MeasurementConfig("file:///tmp/image.jpg")
