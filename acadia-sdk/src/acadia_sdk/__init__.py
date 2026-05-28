"""IV&V Python SDK — a Pythonic gRPC client for the Acadia ``HalService``.

Public API:

* :func:`connect` — open a :class:`Device` connection.
* :class:`Device` — discovery and lifecycle.
* :class:`Peripheral` — one HAL module's test surface.
* Exception hierarchy rooted in :class:`IVVError`.

Example:
    >>> import acadia_sdk as ivv
    >>> with ivv.connect("192.168.1.50:50051") as dev:
    ...     imu = dev.peripheral("imu")
    ...     result = imu.run_oneshot()
    ...     print(result.output.metrics["accel_x"].double_value)
"""
from __future__ import annotations

from acadia_sdk._version import __contracts_version__, __version__

try:
    from acadia_sdk.client import Device, connect
    from acadia_sdk.exceptions import (
        ConfigError,
        ConnectionError,
        IVVError,
        NotSupported,
        PeripheralNotFound,
        TestError,
        TimeoutError,
    )
    from acadia_sdk.peripheral import LongRunningSession, Peripheral
except ImportError:
    # Generated bindings (acadia_sdk.types) are not present yet — likely
    # being bootstrapped by tools/gen_types.py. Allow the parent package
    # to import so codegen can proceed; the public API is unavailable
    # until `make gen` completes.
    pass

__all__ = [
    "ConfigError",
    "ConnectionError",
    "Device",
    "IVVError",
    "LongRunningSession",
    "NotSupported",
    "Peripheral",
    "PeripheralNotFound",
    "TestError",
    "TimeoutError",
    "__contracts_version__",
    "__version__",
    "connect",
]
