#!/usr/bin/env bash
set -euo pipefail

python examples/langchain_to_agently_map.py
python examples/langgraph_to_agently_triggerflow.py
