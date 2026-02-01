from agently import TriggerFlow, TriggerFlowEventData


def triggerflow_emit_when_collect():
    flow = TriggerFlow()

    @flow.chunk
    async def planner(data: TriggerFlowEventData):
        await data.async_emit("Plan.Read", {"task": "read"})
        await data.async_emit("Plan.Write", {"task": "write"})
        return "plan done"

    @flow.chunk
    def reader(data: TriggerFlowEventData):
        return f"read:{data.value['task']}"

    @flow.chunk
    def writer(data: TriggerFlowEventData):
        return f"write:{data.value['task']}"

    @flow.chunk
    def print_collect(data: TriggerFlowEventData):
        print("collect:", data.value)
        return data.value

    flow.to(planner)
    flow.when("Plan.Read").to(reader).collect("plan", "read")
    flow.when("Plan.Write").to(writer).collect("plan", "write").to(print_collect).end()

    result = flow.start("go")
    print("result:", result)


if __name__ == "__main__":
    triggerflow_emit_when_collect()
