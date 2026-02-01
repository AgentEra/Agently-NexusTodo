from agently import Agently, TriggerFlow, TriggerFlowEventData


Agently.set_settings(
    "OpenAICompatible",
    {
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2.5:7b",
        "model_type": "chat",
    },
)


def plan_execute_basic():
    agent = Agently.create_agent()
    flow = TriggerFlow()

    @flow.chunk
    def build_plan(_: TriggerFlowEventData):
        response = (
            agent.input("Create a 3-step plan for a small product launch.")
            .output({"plan": [(str, "plan steps")]})
            .get_response()
        )
        return response.get_data().get("plan", [])

    @flow.chunk
    def cache_plan(data: TriggerFlowEventData):
        data.set_runtime_data("plan", data.value)
        return data.value

    @flow.chunk
    def execute_step(data: TriggerFlowEventData):
        step_text = str(data.value)
        response = (
            agent.input(f"Execute this step: {step_text}. Provide a one-sentence outcome.")
            .output({"result": (str, "step outcome")})
            .get_response()
        )
        return {"step": step_text, "result": response.get_data()["result"]}

    @flow.chunk
    def build_result(data: TriggerFlowEventData):
        plan = data.get_runtime_data("plan") or []
        return {"plan": plan, "results": data.value}

    (
        flow.to(build_plan)
        .to(cache_plan)
        .for_each(concurrency=1)
        .to(execute_step)
        .end_for_each()
        .to(build_result)
        .end()
    )

    result = flow.start("start")
    print(result)


if __name__ == "__main__":
    plan_execute_basic()
