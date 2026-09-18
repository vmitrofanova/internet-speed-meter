"""Domain objects and aggregation rules for speed measurements."""

from dataclasses import dataclass

BYTES_PER_MEGABYTE = 1_000_000


@dataclass(frozen=True, slots=True)
class DownloadSample:
    """The immutable result of one completed request."""

    sequence_number: int
    elapsed_seconds: float
    downloaded_bytes: int

    def __post_init__(self) -> None:
        if self.sequence_number <= 0:
            raise ValueError("sequence_number must be positive")
        if self.elapsed_seconds <= 0:
            raise ValueError("elapsed_seconds must be positive")
        if self.downloaded_bytes < 0:
            raise ValueError("downloaded_bytes cannot be negative")

    @property
    def downloaded_megabytes(self) -> float:
        return self.downloaded_bytes / BYTES_PER_MEGABYTE

    @property
    def megabytes_per_second(self) -> float:
        return self.downloaded_megabytes / self.elapsed_seconds


@dataclass(frozen=True, slots=True)
class MeasurementReport:
    """Aggregated result of a successful measurement run."""

    samples: tuple[DownloadSample, ...]

    def __post_init__(self) -> None:
        if not self.samples:
            raise ValueError("at least one sample is required")

        expected_numbers = tuple(range(1, len(self.samples) + 1))
        actual_numbers = tuple(sample.sequence_number for sample in self.samples)
        if actual_numbers != expected_numbers:
            raise ValueError("samples must be complete and ordered")

    @property
    def request_count(self) -> int:
        return len(self.samples)

    @property
    def total_seconds(self) -> float:
        return sum(sample.elapsed_seconds for sample in self.samples)

    @property
    def average_request_seconds(self) -> float:
        return self.total_seconds / self.request_count

    @property
    def total_bytes(self) -> int:
        return sum(sample.downloaded_bytes for sample in self.samples)

    @property
    def total_megabytes(self) -> float:
        return self.total_bytes / BYTES_PER_MEGABYTE

    @property
    def average_megabytes_per_second(self) -> float:
        """Return weighted throughput: total bytes divided by total time."""

        return self.total_megabytes / self.total_seconds
