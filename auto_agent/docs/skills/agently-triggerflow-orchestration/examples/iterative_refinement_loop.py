from agently import Agently, TriggerFlow, TriggerFlowEventData


Agently.set_settings(
    "OpenAICompatible",
    {
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2.5:7b",
        "model_type": "chat",
    },
)


def iterative_refinement_loop():
    agent = Agently.create_agent()
    flow = TriggerFlow()
    topic = "the value of structured output"
    max_attempts = 3

    @flow.chunk
    def init_state(data: TriggerFlowEventData):
        data.set_runtime_data("attempt", 0)
        data.set_runtime_data("topic", topic)
        data.set_runtime_data("draft", None)
        return data.value

    @flow.chunk
    def refine_once(data: TriggerFlowEventData):
        attempt = int(data.get_runtime_data("attempt") or 0) + 1
        draft = data.get_runtime_data("draft")
        if not draft:
            draft_resp = (
                agent.input(f"Write a one-sentence description of {topic}.")
                .output({"draft": (str, "one-sentence draft")})
                .get_response()
            )
            draft = draft_resp.get_data()["draft"]

        review_resp = (
            agent.input(
                "Score the copy (1-5), list issues, and provide a clearer rewrite:\n" + draft
            )
            .output(
                {
                    "score": (int, "score (1-5)"),
                    "issues": [(str, "issues")],
                    "improved": (str, "improved version"),
                }
            )
            .get_response()
        )
        review = review_resp.get_data()
        score = int(review.get("score", 0))
        improved = review.get("improved", draft)

        data.set_runtime_data("attempt", attempt)
        data.set_runtime_data("draft", improved)

        print(f"round {attempt} score={score} draft={draft}")

        if score >= 4 or attempt >= max_attempts:
            data.emit("Done", improved)
        else:
            data.emit("Next", None)
        return improved

    @flow.chunk
    def print_final(data: TriggerFlowEventData):
        print("final:", data.value)
        return data.value

    flow.to(init_state).to(refine_once)
    flow.when("Next").to(refine_once)
    flow.when("Done").to(print_final).end()

    flow.start("start", wait_for_result=False)


if __name__ == "__main__":
    iterative_refinement_loop()
