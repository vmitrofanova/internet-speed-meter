"""HTTP transport implementation."""

import http.client
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, Self

USER_AGENT = "internet-speed-meter/2.0 (Python 3.12)"


class Response(Protocol):
    def read(self, size: int = -1) -> bytes: ...

    def __enter__(self) -> Self: ...

    def __exit__(self, *args: object) -> None: ...


class Opener(Protocol):
    def open(self, request: urllib.request.Request, timeout: float) -> Response: ...


@dataclass(frozen=True, slots=True)
class TransferResult:
    elapsed_seconds: float
    downloaded_bytes: int


class DownloadError(RuntimeError):
    """Raised when an HTTP transfer cannot be completed."""


class HttpDownloader:
    """Download response bodies in bounded chunks and measure elapsed time."""

    def __init__(
        self,
        *,
        opener: Opener | None = None,
        clock_ns: Callable[[], int] = time.perf_counter_ns,
    ) -> None:
        self._opener = opener or urllib.request.build_opener()
        self._clock_ns = clock_ns

    def download(
        self,
        url: str,
        *,
        timeout_seconds: float,
        chunk_size: int,
    ) -> TransferResult:
        request = urllib.request.Request(
            url,
            headers={
                "Accept-Encoding": "identity",
                "Cache-Control": "no-cache",
                "User-Agent": USER_AGENT,
            },
        )
        started_at_ns = self._clock_ns()
        downloaded_bytes = 0

        try:
            with self._opener.open(request, timeout=timeout_seconds) as response:
                while chunk := response.read(chunk_size):
                    downloaded_bytes += len(chunk)
        except (
            urllib.error.URLError,
            TimeoutError,
            OSError,
            http.client.HTTPException,
        ) as error:
            raise DownloadError(str(error)) from error

        elapsed_ns = max(self._clock_ns() - started_at_ns, 1)
        return TransferResult(
            elapsed_seconds=elapsed_ns / 1_000_000_000,
            downloaded_bytes=downloaded_bytes,
        )
