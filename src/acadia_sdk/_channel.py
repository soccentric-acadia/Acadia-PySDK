"""Private gRPC channel management and error translation.

This module is the SDK's single chokepoint for talking to the peer. Every
call goes through :func:`call_unary` or :func:`call_stream`, which catch
``grpc.RpcError`` and translate to :mod:`acadia_sdk.exceptions`.
"""
from __future__ import annotations

import logging
from collections.abc import Callable, Iterator
from contextlib import suppress
from typing import Any, TypeVar

import grpc

from acadia_sdk import exceptions as exc
from acadia_sdk._version import __contracts_version__

log = logging.getLogger(__name__)

T = TypeVar("T")

# Mapping from gRPC status codes to SDK exception classes.
_STATUS_TO_EXC: dict[grpc.StatusCode, type[exc.IVVError]] = {
    grpc.StatusCode.UNAVAILABLE: exc.ConnectionError,
    grpc.StatusCode.DEADLINE_EXCEEDED: exc.TimeoutError,
    grpc.StatusCode.NOT_FOUND: exc.PeripheralNotFound,
    grpc.StatusCode.INVALID_ARGUMENT: exc.ConfigError,
    grpc.StatusCode.UNIMPLEMENTED: exc.NotSupported,
    grpc.StatusCode.FAILED_PRECONDITION: exc.ConfigError,
    grpc.StatusCode.PERMISSION_DENIED: exc.ConnectionError,
    grpc.StatusCode.UNAUTHENTICATED: exc.ConnectionError,
    grpc.StatusCode.CANCELLED: exc.IVVError,
    grpc.StatusCode.ABORTED: exc.TestError,
}


def open_channel(
    address: str,
    *,
    options: list[tuple[str, Any]] | None = None,
    tls: bool = False,
) -> grpc.Channel:
    """Open a gRPC channel with optional TLS.

    Task 99: when ``tls=True`` the channel uses TLS credentials so the peer's
    listener (loopback / authenticated transport) can reject plaintext.
    Plaintext remains the default for the closed lab subnet.
    """
    if not address:
        raise exc.ConnectionError("address must be a non-empty 'host:port' string")
    if ":" not in address:
        raise exc.ConnectionError(f"address must include a port: {address!r}")
    if tls:
        return grpc.secure_channel(address, grpc.ssl_channel_credentials(), options=options or [])
    return grpc.insecure_channel(address, options=options or [])


def _translate_rpc_error(rpc_err: grpc.RpcError) -> exc.IVVError:
    code: grpc.StatusCode = rpc_err.code() if hasattr(rpc_err, "code") else grpc.StatusCode.UNKNOWN
    detail: str | None = rpc_err.details() if hasattr(rpc_err, "details") else str(rpc_err)
    cls = _STATUS_TO_EXC.get(code, exc.IVVError)
    msg = f"{code.name if code else 'UNKNOWN'}: {detail or ''}"
    return cls(msg)


def call_unary(stub_method: Callable[..., T], request: Any, *, timeout: float | None = None,
               metadata: tuple[tuple[str, str], ...] | None = None) -> T:
    """Invoke a unary RPC, translating gRPC errors to SDK exceptions.

    ``metadata`` (optional) carries auth/session metadata to the peer (task 99).
    """
    try:
        return stub_method(request, timeout=timeout, metadata=metadata)
    except grpc.RpcError as rpc_err:
        raise _translate_rpc_error(rpc_err) from rpc_err


def call_stream(
    stub_method: Callable[..., Iterator[T]],
    request: Any,
    *,
    timeout: float | None = None,
) -> Iterator[T]:
    """Iterate a server-streaming RPC, translating gRPC errors to SDK exceptions.

    The returned generator must be consumed (or explicitly closed) for the
    underlying gRPC call to release resources.
    """
    try:
        call = stub_method(request, timeout=timeout)
    except grpc.RpcError as rpc_err:
        raise _translate_rpc_error(rpc_err) from rpc_err
    try:
        yield from call
    except grpc.RpcError as rpc_err:
        raise _translate_rpc_error(rpc_err) from rpc_err
    finally:
        with suppress(Exception):
            call.cancel()  # type: ignore[attr-defined]


# Task 98: bound the stream so a slow consumer cannot grow an unbounded buffer,
# and make cancellation/shutdown/close deterministic. `bounded_stream` reads the
# underlying gRPC call into a fixed-capacity deque; if the consumer is slower
# than the producer past the cap, it applies backpressure (blocks the reader)
# rather than buffering without limit.
def bounded_stream(
    stub_method: Callable[..., Iterator[object]],
    request: Any,
    *,
    timeout: float | None = None,
    max_buffer: int = 256,
) -> Iterator[object]:
    """Task 98: bound a server stream so a slow consumer cannot grow an unbounded
    buffer, and make cancellation/shutdown/close deterministic (idempotent).
    Uses a Condition so no wakeup is lost; backpressure is applied once the
    buffer is at capacity instead of buffering without limit.
    """
    from collections import deque
    from threading import Condition, Thread

    buf: deque[object] = deque(maxlen=max_buffer)
    cond = Condition()
    done = False
    err: list[BaseException | None] = [None]
    closed = [False]

    def pump() -> None:
        nonlocal done
        try:
            call = stub_method(request, timeout=timeout)
        except grpc.RpcError as e:
            err[0] = _translate_rpc_error(e)
            with cond:
                done = True
                cond.notify_all()
            return
        try:
            for item in call:
                with cond:
                    while len(buf) >= max_buffer and not closed[0]:
                        cond.wait(timeout=0.1)
                    if closed[0]:
                        with suppress(Exception):
                            call.cancel()  # type: ignore[attr-defined]
                        return
                    buf.append(item)
                    cond.notify_all()
        except grpc.RpcError as e:
            err[0] = _translate_rpc_error(e)
        finally:
            with suppress(Exception):
                call.cancel()  # type: ignore[attr-defined]
            with cond:
                done = True
                cond.notify_all()

    t = Thread(target=pump, daemon=True)
    t.start()
    try:
        while True:
            with cond:
                while not buf and not done and err[0] is None and not closed[0]:
                    cond.wait()
                if buf:
                    item = buf.popleft()
                    cond.notify_all()  # wake pump waiting on backpressure
                else:
                    item = None
            if item is not None:
                yield item
                continue
            if err[0] is not None:
                raise err[0]
            return
    finally:
        with cond:
            closed[0] = True
            done = True
            cond.notify_all()


def handshake_modules(modules: list[Any]) -> None:
    """Verify every advertised module's version is within the SDK's support
    window. Raises :class:`ConnectionError` if any module is too new.
    """
    too_new: list[str] = []
    for m in modules:
        if int(getattr(m, "version", 1)) > __contracts_version__:
            too_new.append(f"{m.id}=v{m.version}")
    if too_new:
        joined = ", ".join(too_new)
        raise exc.ConnectionError(
            f"peer advertises modules with contract versions newer than this SDK "
            f"supports (max v{__contracts_version__}): {joined}. "
            "Upgrade acadia-sdk to match."
        )
