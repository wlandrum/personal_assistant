from assistant.agents.router import classify


class FakeProvider:
    def __init__(self, reply):
        self.reply = reply

    def complete(self, prompt, system=None):
        return self.reply


def test_router_detects_note():
    assert classify(FakeProvider("note"), "things to do: call mom, buy milk") == "note"


def test_router_defaults_to_chat():
    assert classify(FakeProvider("something unexpected"), "what time is it") == "chat"
