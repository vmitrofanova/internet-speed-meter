"""Validated application configuration."""

from dataclasses import dataclass
from urllib.parse import urlsplit

DEFAULT_REQUEST_COUNT = 10
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_CHUNK_SIZE = 64 * 1024


@dataclass(frozen=True, slots=True)
class MeasurementConfig:
    """Settings required to execute one complete measurement."""

    url: str
    request_count: int = DEFAULT_REQUEST_COUNT
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    chunk_size: int = DEFAULT_CHUNK_SIZE

    def __post_init__(self) -> None:
        parsed_url = urlsplit(self.url)
        if (
            parsed_url.scheme.lower() not in {"http", "https"}
            or not parsed_url.hostname
        ):
            raise ValueError(
                "адрес должен быть полным HTTP(S) URL, "
                "например https://example.com/image.jpg"
            )
        if self.request_count <= 0:
            raise ValueError("количество запросов должно быть больше нуля")
        if self.timeout_seconds <= 0:
            raise ValueError("тайм-аут должен быть больше нуля")
        if self.chunk_size <= 0:
            raise ValueError("размер блока должен быть больше нуля")
