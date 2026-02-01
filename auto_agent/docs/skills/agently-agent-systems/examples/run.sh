#!/usr/bin/env bash
set -euo pipefail

python examples/structured_output_with_ensure_keys.py
python examples/order_and_dependencies_output.py
python examples/triggerflow_emit_when_collect.py
python examples/triggerflow_runtime_data_collect.py
python examples/plan_execute_basic.py
python examples/react_tool_loop.py
python examples/multi_agent_router.py
python examples/rag_with_info_prompt.py
# FastAPI service example (uncomment to run server)
# python examples/fastapi_triggerflow_service.py
