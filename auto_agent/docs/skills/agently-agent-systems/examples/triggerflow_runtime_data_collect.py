from agently import TriggerFlow, TriggerFlowEventData


def triggerflow_runtime_data_collect():
    flow = TriggerFlow()

    @flow.chunk
    def set_user(data: TriggerFlowEventData):
        data.set_runtime_data("user_id", "u-001")
        return "user_ok"

    @flow.chunk
    def set_env(data: TriggerFlowEventData):
        data.set_runtime_data("env", "prod")
        return "env_ok"

    @flow.chunk
    def on_user(data: TriggerFlowEventData):
        return {"user_id": data.value}

    @flow.chunk
    def on_env(data: TriggerFlowEventData):
        return {"env": data.value}

    @flow.chunk
    def print_collect(data: TriggerFlowEventData):
        print("collect:", data.value)
        return data.value

    flow.when({"runtime_data": "user_id"}).to(on_user)
    flow.when({"runtime_data": "env"}).to(on_env)

    flow.to(set_user).collect("ready", "user")
    flow.to(set_env).collect("ready", "env").to(print_collect).end()

    result = flow.start("start")
    print("result:", result)


if __name__ == "__main__":
    triggerflow_runtime_data_collect()
