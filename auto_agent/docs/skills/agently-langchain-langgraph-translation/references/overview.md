# Translation References

This skill focuses on translating LangChain/LangGraph structures into Agently patterns.

Mapping anchors:
- PromptTemplate -> agent prompt layers + mappings
- LLMChain -> agent input/output + start()
- OutputParser -> Output Format + ensure_keys
- Tool -> @agent.tool_func + use_tool()
- Graph node -> TriggerFlow chunk
- Graph edge -> TriggerFlow when/to/if/match/collect

Source references:
- LangChain tools overview: https://docs.langchain.com/oss/python/langchain-tools
- LangChain tool calling + bind_tools: https://python.langchain.com/docs/concepts/tool_calling/
- LangGraph quickstart / StateGraph basics: https://docs.langchain.com/oss/python/langgraph
