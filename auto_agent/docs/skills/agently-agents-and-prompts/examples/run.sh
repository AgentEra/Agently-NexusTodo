#!/usr/bin/env bash
set -euo pipefail

python examples/prompt_layers_and_mappings.py
python examples/prompt_config_from_yaml.py
python examples/multi_agent_router.py
python examples/rag_with_info_prompt.py
python examples/single_request_multi_read.py
