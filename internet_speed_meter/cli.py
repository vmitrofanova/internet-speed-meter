"""Command-line interface."""

import argparse
import sys
from collections.abc import Sequence
from typing import TextIO

from .config import (
    DEFAULT_REQUEST_COUNT,
    DEFAULT_TIMEOUT_SECONDS,
    MeasurementConfig,
)
from .domain import DownloadSample, MeasurementReport
from .service import MeasurementError, SpeedMeter


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("ожидается целое число") from error
    if number <= 0:
        raise argparse.ArgumentTypeError("значение должно быть больше нуля")
    return number


def positive_float(value: str) -> float:
    try:
        number = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("ожидается число") from error
    if number <= 0:
        raise argparse.ArgumentTypeError("значение должно быть больше нуля")
    return number


def http_url(value: str) -> str:
    try:
        MeasurementConfig(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Последовательно скачивает файл и измеряет среднее время, объём данных "
            "и скорость загрузки."
        )
    )
    parser.add_argument("url", type=http_url, help="URL тяжёлого файла или изображения")
    parser.add_argument(
        "-n",
        "--requests",
        type=positive_int,
        default=DEFAULT_REQUEST_COUNT,
        help=f"количество запросов (по умолчанию: {DEFAULT_REQUEST_COUNT})",
    )
    parser.add_argument(
        "--timeout",
        type=positive_float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=(
            "тайм-аут одного запроса в секундах "
            f"(по умолчанию: {DEFAULT_TIMEOUT_SECONDS:g})"
        ),
    )
    return parser


def print_sample(sample: DownloadSample, request_count: int, output: TextIO) -> None:
    print(
        f"Запрос {sample.sequence_number:>2}/{request_count}: "
        f"{sample.elapsed_seconds:.3f} с, "
        f"{sample.downloaded_megabytes:.3f} МБ, "
        f"{sample.megabytes_per_second:.3f} МБ/с",
        file=output,
        flush=True,
    )


def print_report(report: MeasurementReport, output: TextIO) -> None:
    print("\nИтого:", file=output)
    print(
        f"  Среднее время запроса: {report.average_request_seconds:.3f} с",
        file=output,
    )
    print(
        f"  Скачано данных:        {report.total_megabytes:.3f} МБ "
        f"({report.total_bytes} байт)",
        file=output,
    )
    print(
        f"  Средняя скорость:      {report.average_megabytes_per_second:.3f} МБ/с",
        file=output,
    )


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
    speed_meter: SpeedMeter | None = None,
) -> int:
    args = build_parser().parse_args(argv)
    config = MeasurementConfig(
        url=args.url,
        request_count=args.requests,
        timeout_seconds=args.timeout,
    )

    print(f"Адрес: {config.url}", file=stdout)
    print(f"Последовательных запросов: {config.request_count}\n", file=stdout)

    meter = speed_meter or SpeedMeter()
    try:
        report = meter.run(
            config,
            on_progress=lambda sample, count: print_sample(sample, count, stdout),
        )
    except MeasurementError as error:
        print(f"\nОшибка измерения: {error}", file=stderr)
        return 1

    print_report(report, stdout)
    return 0
