#!/usr/bin/env bash
set -euo pipefail

python examples/standard_trigger_flow_usage.py
python examples/triggerflow_emit_when_collect.py
python examples/triggerflow_runtime_data_collect.py
python examples/plan_execute_basic.py
python examples/iterative_refinement_loop.py
