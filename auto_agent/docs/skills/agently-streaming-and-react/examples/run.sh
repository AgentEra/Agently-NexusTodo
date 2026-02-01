#!/usr/bin/env bash
set -euo pipefail

python examples/streaming_with_instant_mode.py
python examples/response_event_streams.py
python examples/trigger_flow_with_agent.py
printf 'What is structured output?\nexit\n' | python examples/react_tool_loop.py
