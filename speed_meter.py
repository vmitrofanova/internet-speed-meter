#!/usr/bin/env python3
"""Compatibility entry point for running the project without installation."""

from internet_speed_meter.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
