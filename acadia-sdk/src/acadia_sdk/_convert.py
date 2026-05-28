"""Private helpers for unpacking ``google.protobuf.Any`` payloads into
the correct typed dataclass for a module's ``Result`` message.
"""
from __future__ import annotations

import importlib
from typing import Any

from google.protobuf.message import Message

# Lazy cache: module_id -> (dataclass, pb_class) for that module's Result.
_RESULT_CACHE: dict[str, tuple[type, type[Message]]] = {}


def _load(module_id: str) -> tuple[type, type[Message]]:
    """Look up the ``Result`` dataclass and its underlying pb class for
    ``module_id`` (e.g. ``"imu"``)."""
    if module_id in _RESULT_CACHE:
        return _RESULT_CACHE[module_id]
    try:
        types_mod = importlib.import_module(f"acadia_sdk.types.modules.{module_id}")
        pb_mod = importlib.import_module(f"acadia_sdk._proto.modules.{module_id}_pb2")
    except ModuleNotFoundError as e:
        raise LookupError(f"no typed bindings for module {module_id!r}") from e
    dc = types_mod.Result
    pb = pb_mod.Result
    _RESULT_CACHE[module_id] = (dc, pb)
    return dc, pb


def unpack_result(envelope: Any) -> Any:
    """Decode a ``ResultEnvelope`` (typed dataclass) into the module-specific
    ``Result`` dataclass. Returns the dataclass instance.

    Falls back to the raw envelope payload if the module is unknown.
    """
    payload = envelope.payload  # AnyMessage dataclass
    if not payload.type_url:
        return None
    full_name = payload.type_url.split("/")[-1]
    # ``hal.modules.imu.Result`` → ``imu``
    parts = full_name.split(".")
    if len(parts) >= 3 and parts[0] == "hal" and parts[1] == "modules":
        module_id = parts[2]
    else:
        return payload
    dc, pb = _load(module_id)
    pb_msg = pb()
    pb_msg.ParseFromString(payload.value)
    dc_any: object = dc
    return dc_any.from_proto(pb_msg)  # type: ignore[attr-defined]


def pack_module_config(module_id: str, config_dc: Any) -> Any:
    """Serialise a module's ``Config`` dataclass into a ``google.protobuf.Any``
    dataclass with the proper type URL."""
    from acadia_sdk.types._runtime import AnyMessage

    pb = config_dc.to_proto()
    type_url = f"type.googleapis.com/{pb.DESCRIPTOR.full_name}"
    return AnyMessage(type_url=type_url, value=pb.SerializeToString())


def load_config_class(module_id: str) -> type:
    """Return the dataclass for ``hal.modules.<module_id>.Config``."""
    try:
        types_mod = importlib.import_module(f"acadia_sdk.types.modules.{module_id}")
    except ModuleNotFoundError as e:
        raise LookupError(f"no typed bindings for module {module_id!r}") from e
    cls = types_mod.Config
    assert isinstance(cls, type)
    return cls
