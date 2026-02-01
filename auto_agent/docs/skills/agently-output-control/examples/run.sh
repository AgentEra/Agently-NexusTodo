#!/usr/bin/env bash
set -euo pipefail

python examples/structured_output_with_ensure_keys.py
python examples/order_and_dependencies_output.py
python examples/streaming_with_instant_mode.py
python examples/response_event_streams.py
python examples/key_waiter_early_field.py
