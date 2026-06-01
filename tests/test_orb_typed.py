from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vss.orb.typed import _parse_primitive


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("ON", True),
        ("OFF", False),
        ("42", 42),
        ("-17", -17),
        ("3.5", 3.5),
        ("1.2e3", 1200.0),
        ('"hello world"', "hello world"),
        ("'quoted'", "quoted"),
        ("ONWARD", "ONWARD"),
        ("1.2.3", "1.2.3"),
        ("'unterminated", "'unterminated"),
        ("nan", "nan"),
        ("inf", "inf"),
    ],
)
def test_parse_primitive(token: str, expected) -> None:
    assert _parse_primitive(token) == expected
