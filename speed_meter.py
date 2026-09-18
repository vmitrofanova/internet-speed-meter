#!/usr/bin/env python3
"""Measure download speed by fetching the same URL sequentially."""

from __future__ import annotations

import argparse
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Callable, Sequence


DEFAULT_REQUESTS = 10
DEFAULT_TIMEOUT_SECONDS = 30.0
CHUNK_SIZE = 64 * 1024
BYTES_PER_MEGABYTE = 1_000_000


@dataclass(frozen=True)
class RequestResult:
    elapsed_seconds: float
    downloaded_bytes: int


def validate_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise argparse.ArgumentTypeError(
            "адрес должен быть полным HTTP(S) URL, например https://example.com/image.jpg"
        )
    return url


def download_once(
    url: str,
    timeout: float,
    *,
    clock: Callable[[], float] = time.perf_counter,
) -> RequestResult:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "internet-speed-meter/1.0"},
    )
    started_at = clock()
    downloaded_bytes = 0

    with urllib.request.urlopen(request, timeout=timeout) as response:
        while chunk := response.read(CHUNK_SIZE):
            downloaded_bytes += len(chunk)

    elapsed_seconds = clock() - started_at
    return RequestResult(elapsed_seconds, downloaded_bytes)


def measure(
    url: str,
    request_count: int,
    timeout: float,
    *,
    output: Callable[[str], None] = print,
) -> list[RequestResult]:
    results: list[RequestResult] = []

    for number in range(1, request_count + 1):
        result = download_once(url, timeout)
        results.append(result)
        megabytes = result.downloaded_bytes / BYTES_PER_MEGABYTE
        speed = megabytes / result.elapsed_seconds if result.elapsed_seconds else float("inf")
        output(
            f"Запрос {number:>2}/{request_count}: "
            f"{result.elapsed_seconds:.3f} с, {megabytes:.3f} МБ, {speed:.3f} МБ/с"
        )

    return results


def print_summary(results: Sequence[RequestResult]) -> None:
    total_seconds = sum(result.elapsed_seconds for result in results)
    total_bytes = sum(result.downloaded_bytes for result in results)
    average_seconds = total_seconds / len(results)
    total_megabytes = total_bytes / BYTES_PER_MEGABYTE
    average_speed = total_megabytes / total_seconds if total_seconds else float("inf")

    print("\nИтого:")
    print(f"  Среднее время запроса: {average_seconds:.3f} с")
    print(f"  Скачано данных:        {total_megabytes:.3f} МБ ({total_bytes} байт)")
    print(f"  Средняя скорость:      {average_speed:.3f} МБ/с")


def positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("значение должно быть больше нуля")
    return number


def positive_float(value: str) -> float:
    number = float(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("значение должно быть больше нуля")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Последовательно скачивает файл и измеряет среднее время, объём данных "
            "и скорость загрузки."
        )
    )
    parser.add_argument("url", type=validate_url, help="URL тяжёлого файла или изображения")
    parser.add_argument(
        "-n",
        "--requests",
        type=positive_int,
        default=DEFAULT_REQUESTS,
        help=f"количество запросов (по умолчанию: {DEFAULT_REQUESTS})",
    )
    parser.add_argument(
        "--timeout",
        type=positive_float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"тайм-аут одного запроса в секундах (по умолчанию: {DEFAULT_TIMEOUT_SECONDS:g})",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(f"Адрес: {args.url}")
    print(f"Последовательных запросов: {args.requests}\n")

    try:
        results = measure(args.url, args.requests, args.timeout)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        print(f"\nОшибка загрузки: {error}", file=sys.stderr)
        return 1

    print_summary(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
