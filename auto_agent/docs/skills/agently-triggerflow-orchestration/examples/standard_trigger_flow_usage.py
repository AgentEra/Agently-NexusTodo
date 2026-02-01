from agently import TriggerFlow, TriggerFlowEventData


def standard_trigger_flow_usage():
    flow = TriggerFlow()

    @flow.chunk("normalize_input")
    def normalize_input(data: TriggerFlowEventData):
        text = str(data.value).strip().lower()
        return {"text": text}

    @flow.chunk
    def intent_refund(data: TriggerFlowEventData):
        return {**data.value, "intent": "refund"}

    @flow.chunk
    def intent_bug(data: TriggerFlowEventData):
        return {**data.value, "intent": "bug"}

    @flow.chunk
    def intent_other(data: TriggerFlowEventData):
        return {**data.value, "intent": "other"}

    @flow.chunk
    def set_priority_high(data: TriggerFlowEventData):
        return {**data.value, "priority": "high"}

    @flow.chunk
    def set_priority_normal(data: TriggerFlowEventData):
        return {**data.value, "priority": "normal"}

    @flow.chunk("draft_reply")
    def draft_reply(data: TriggerFlowEventData):
        reply = f"We received a {data.value['intent']} request and will process it soon."
        return {"priority": data.value["priority"], "reply": reply}

    @flow.chunk("extract_keywords")
    def extract_keywords(data: TriggerFlowEventData):
        text = data.value["text"].replace("#", " ")
        keywords = [word for word in text.split() if word.isalpha()]
        return {"priority": data.value["priority"], "keywords": keywords[:3]}

    @flow.chunk
    def merge_batch(data: TriggerFlowEventData):
        reply = data.value["draft_reply"]["reply"]
        keywords = data.value["extract_keywords"]["keywords"]
        priority = data.value["draft_reply"]["priority"]
        return {"priority": priority, "reply": reply, "keywords": keywords}

    @flow.chunk
    def print_result(data: TriggerFlowEventData):
        print(data.value)
        return data.value

    (
        flow.to("normalize_input")
        .match()
        .case(lambda d: "refund" in d.value["text"])
        .to(intent_refund)
        .case(lambda d: "bug" in d.value["text"])
        .to(intent_bug)
        .case_else()
        .to(intent_other)
        .end_match()
        .if_condition(lambda d: "urgent" in d.value["text"] or "asap" in d.value["text"])
        .to(set_priority_high)
        .else_condition()
        .to(set_priority_normal)
        .end_condition()
        .batch(draft_reply, extract_keywords)
        .to(merge_batch)
        .to(print_result)
        .end()
    )

    result = flow.start("URGENT refund request for order #123, please help ASAP")
    print("final_result:", result)


if __name__ == "__main__":
    standard_trigger_flow_usage()
