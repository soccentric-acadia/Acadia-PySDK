"""02 — Run a one-shot test on the IMU peripheral."""
from __future__ import annotations

import sys

import acadia_sdk


def main(address: str) -> None:
    with acadia_sdk.connect(address) as dev:
        imu = dev.peripheral("imu")
        result = imu.run_oneshot()
        for tr in result.results:
            print(f"{tr.name:<20} status={tr.output.status.name}")
            for key, value in tr.output.metrics.items():
                # TypedValue is a oneof; show whichever arm carries the data.
                pretty = (
                    value.double_value
                    if value.double_value != 0.0
                    else value.bool_value
                    if value.bool_value
                    else value.int_value
                    if value.int_value
                    else value.string_value
                )
                print(f"    {key:<18} = {pretty!r}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1:50051")
