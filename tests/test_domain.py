import unittest

from internet_speed_meter.domain import DownloadSample, MeasurementReport


class MeasurementReportTests(unittest.TestCase):
    def test_aggregates_weighted_throughput(self) -> None:
        report = MeasurementReport(
            (
                DownloadSample(1, elapsed_seconds=1.0, downloaded_bytes=1_000_000),
                DownloadSample(2, elapsed_seconds=3.0, downloaded_bytes=9_000_000),
            )
        )

        self.assertEqual(report.request_count, 2)
        self.assertEqual(report.total_bytes, 10_000_000)
        self.assertEqual(report.average_request_seconds, 2.0)
        self.assertEqual(report.average_megabytes_per_second, 2.5)

    def test_rejects_missing_or_out_of_order_samples(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one"):
            MeasurementReport(())
        with self.assertRaisesRegex(ValueError, "complete and ordered"):
            MeasurementReport((DownloadSample(2, 1.0, 100),))

    def test_rejects_non_positive_duration(self) -> None:
        with self.assertRaisesRegex(ValueError, "elapsed_seconds"):
            DownloadSample(1, 0.0, 100)
