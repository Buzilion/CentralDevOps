#!/usr/bin/env python3
"""Encode raw SSH private-key bytes for the VPS bootstrap secret."""

from __future__ import annotations

import base64
import sys

BASE64_PRIVATE_KEY_PREFIX = b"base64:"


def main() -> int:
    private_key = sys.stdin.buffer.read()
    if not private_key:
        print("error: SSH private-key input is empty", file=sys.stderr)
        return 1

    encoded_key = BASE64_PRIVATE_KEY_PREFIX + base64.b64encode(private_key)
    sys.stdout.buffer.write(encoded_key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
