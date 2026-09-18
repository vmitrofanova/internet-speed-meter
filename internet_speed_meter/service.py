"""Application service orchestrating sequential downloads."""

from collections.abc import Callable
from typing import Protocol

from .config import MeasurementConfig
from .domain import DownloadSample, MeasurementReport
from .http import DownloadError, HttpDownloader, TransferResult


class Downloader(Protocol):
    def download(
        self,
        url: str,
        *,
        timeout_seconds: float,
        chunk_size: int,
    ) -> TransferResult: ...


type ProgressObserver = Callable[[DownloadSample, int], None]


class MeasurementError(RuntimeError):
    """A measurement aborted because one request did not complete."""

    def __init__(self, request_number: int, request_count: int, reason: str) -> None:
        self.request_number = request_number
        self.request_count = request_count
        super().__init__(
            f"запрос {request_number}/{request_count} не завершён: {reason}"
        )


class SpeedMeter:
    """Execute an all-or-nothing series of sequential download measurements."""

    def __init__(self, downloader: Downloader | None = None) -> None:
        self._downloader = downloader or HttpDownloader()

    def run(
        self,
        config: MeasurementConfig,
        *,
        on_progress: ProgressObserver | None = None,
    ) -> MeasurementReport:
        samples: list[DownloadSample] = []

        for request_number in range(1, config.request_count + 1):
            try:
                transfer = self._downloader.download(
                    config.url,
                    timeout_seconds=config.timeout_seconds,
                    chunk_size=config.chunk_size,
                )
            except DownloadError as error:
                raise MeasurementError(
                    request_number,
                    config.request_count,
                    str(error),
                ) from error

            sample = DownloadSample(
                sequence_number=request_number,
                elapsed_seconds=transfer.elapsed_seconds,
                downloaded_bytes=transfer.downloaded_bytes,
            )
            samples.append(sample)
            if on_progress is not None:
                on_progress(sample, config.request_count)

        return MeasurementReport(tuple(samples))
