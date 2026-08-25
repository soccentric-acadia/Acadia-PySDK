"""Unit tests for the bounded stream iterator (task 98)."""
from __future__ import annotations

from typing import Iterator

from acadia_sdk import _channel


def _stub_stream(items: list[int]) -> Iterator[int]:
    def method(_request: object, *, timeout: float | None = None) -> Iterator[object]:
        for i in items:
            yield i
    return method  # type: ignore[return-value]


def test_bounded_stream_yields_all_items() -> None:
    got = list(_channel.bounded_stream(_stub_stream([1, 2, 3]), None))
    assert got == [1, 2, 3]


def test_bounded_stream_closes_idempotently() -> None:
    # Consuming partially then abandoning (generator close) must not hang or
    # error; close is idempotent.
    gen = _channel.bounded_stream(_stub_stream(range(100)), None)
    first = next(gen)
    assert first == 0
    gen.close()  # idempotent close
    gen.close()
