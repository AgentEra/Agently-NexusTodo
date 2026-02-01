from agently import TriggerFlow, TriggerFlowEventData


LANGGRAPH_SNIPPET = """
from langgraph.graph import StateGraph, MessagesState, START, END

def demo_llm(state: MessagesState):
    return {"messages": [{"role": "ai", "content": "hello"}]}

builder = StateGraph(MessagesState)
builder.add_node("demo_llm", demo_llm)
builder.add_edge(START, "demo_llm")
builder.add_edge("demo_llm", END)
graph = builder.compile()

graph.invoke({"messages": [{"role": "user", "content": "hi there"}]})
"""


def langgraph_to_agently_triggerflow():
    print("LangGraph example (reference, adapted from docs):")
    print(LANGGRAPH_SNIPPET.strip())

    flow = TriggerFlow()

    @flow.chunk
    def plan(_: TriggerFlowEventData):
        return ["step-1", "step-2"]

    @flow.chunk
    def execute(data: TriggerFlowEventData):
        return f"done:{data.value}"

    @flow.chunk
    def collect(data: TriggerFlowEventData):
        print({"results": data.value})
        return data.value

    (
        flow.to(plan)
        .for_each(concurrency=1)
        .to(execute)
        .end_for_each()
        .to(collect)
        .end()
    )

    flow.start("start")


if __name__ == "__main__":
    langgraph_to_agently_triggerflow()
