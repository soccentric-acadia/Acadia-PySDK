"""Tests for the generated dataclass round-trip and JSON serialisation."""
from __future__ import annotations

import json

from acadia_sdk._proto import common_pb2
from acadia_sdk.types import common as common_types


def test_test_result_roundtrip() -> None:
    pb = common_pb2.TestResult(module_id="imu", test_id="t", name="accel_read")
    pb.output.status = common_pb2.TEST_STATUS_PASS
    pb.output.metrics["x"].double_value = 1.5
    pb.output.metrics["calibrated"].bool_value = True
    dc = common_types.TestResult.from_proto(pb)
    assert dc.module_id == "imu"
    assert dc.output.metrics["x"].double_value == 1.5
    # round-trip preserves oneof arm
    pb2 = dc.to_proto()
    assert pb2.output.metrics["x"].double_value == 1.5
    assert pb2.output.metrics["calibrated"].bool_value is True


def test_to_json_serialises_enum_names() -> None:
    pb = common_pb2.TestResult(module_id="imu")
    pb.output.status = common_pb2.TEST_STATUS_PASS
    dc = common_types.TestResult.from_proto(pb)
    payload = json.loads(dc.to_json())
    assert payload["output"]["status"] == "TEST_STATUS_PASS"


def test_to_dict_is_jsonable() -> None:
    pb = common_pb2.TestResult(module_id="imu")
    dc = common_types.TestResult.from_proto(pb)
    d = dc.to_dict()
    json.dumps(d)  # must not raise
