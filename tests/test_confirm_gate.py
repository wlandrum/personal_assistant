from assistant.agents.actions import PendingAction


class FakeSubagent:
    name = "calendar"

    def __init__(self):
        self.ran = False

    def handle(self, owner_id, message):
        def execute():
            self.ran = True
            return "did the thing"
        return PendingAction(summary="will do the thing", execute=execute)


def make_orch(monkeypatch, fake):
    import assistant.orchestrator.orchestrator as o
    monkeypatch.setattr(o, "classify", lambda provider, message: "calendar")
    monkeypatch.setattr(o, "get_provider", lambda settings, tier: object())
    orch = o.Orchestrator.__new__(o.Orchestrator)
    orch.settings = None
    orch.subagents = {"calendar": fake}
    orch.pending = {}
    return orch


def test_confirm_executes(monkeypatch):
    fake = FakeSubagent()
    orch = make_orch(monkeypatch, fake)
    first = orch.respond("u1", "schedule something")
    assert "will do the thing" in first
    assert fake.ran is False
    second = orch.respond("u1", "confirm")
    assert fake.ran is True
    assert "did the thing" in second


def test_cancel_does_not_execute(monkeypatch):
    fake = FakeSubagent()
    orch = make_orch(monkeypatch, fake)
    orch.respond("u1", "schedule something")
    result = orch.respond("u1", "cancel")
    assert fake.ran is False
    assert "Cancelled" in result


def test_pending_is_per_owner(monkeypatch):
    fake = FakeSubagent()
    orch = make_orch(monkeypatch, fake)
    orch.respond("u1", "schedule something")
    orch.respond("u2", "confirm")
    assert fake.ran is False
