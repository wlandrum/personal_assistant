import os
from assistant.data.store import UserStore
from assistant.config import Settings
from assistant.llm.factory import get_provider
from assistant.llm.escalation import provider_for
from assistant.finance.categorize import categorize
from assistant.finance.charts import category_bar


class FinanceSubagent:
    name = "finance"

    def __init__(self, conn, settings: Settings, embedder=None):
        self.conn = conn
        self.settings = settings

    def _intent(self, message: str) -> str:
        prompt = (
            "Classify the finance request as one word: sync, analyze, or goal. "
            "sync means update or pull transactions. analyze means show spending or a breakdown. "
            "goal means plan toward a savings or budget goal.\n\n" + message
        )
        small = get_provider(self.settings, "router")
        answer = small.complete(prompt).strip().lower()
        if "goal" in answer:
            return "goal"
        if "analyze" in answer or "analy" in answer:
            return "analyze"
        return "sync"

    def handle(self, owner_id: str, message: str) -> str:
        intent = self._intent(message)
        if intent == "analyze":
            return self._analyze(owner_id)
        if intent == "goal":
            return self._goal(owner_id, message)
        token = UserStore(self.conn, owner_id).get_credential("plaid")
        if not token:
            return "No bank connection found. Run connect_plaid for sandbox, or import a CSV with import_csv."
        from assistant.finance.plaid_client import build_plaid_client
        from assistant.finance.plaid_source import PlaidSource
        client = build_plaid_client(self.settings.finance.plaid_env)
        return self._ingest(owner_id, PlaidSource(token, client))

    def _ingest(self, owner_id: str, source) -> str:
        store = UserStore(self.conn, owner_id)
        txns = source.fetch()
        added = store.add_transactions(source.source_name, txns)
        rows = store.get_uncategorized()
        pairs = categorize(store, self.settings, rows)
        for txn_id, cat in pairs:
            store.set_category(txn_id, cat)
        store.add_audit("finance_sync", f"source={source.source_name} added={added} categorized={len(pairs)}")
        return f"Synced {added} new transactions from {source.source_name} and categorized {len(pairs)}."

    def _analyze(self, owner_id: str) -> str:
        store = UserStore(self.conn, owner_id)
        by_cat = store.spending_by_category()
        if not by_cat:
            return "No categorized spending found yet. Sync or import transactions first."

        chart_path = os.path.join(self.settings.charts_dir, f"spending_{owner_id}.png")
        category_bar(by_cat, chart_path)

        listing = "\n".join(f"{d['category']}: {d['total']:.2f}" for d in by_cat)
        workhorse = get_provider(self.settings, "workhorse")
        narrative = workhorse.complete(
            "Write a short, neutral two to three sentence summary of this spending breakdown, "
            "noting the largest categories.\n\n" + listing
        )

        store.add_audit("finance_analyze", f"{len(by_cat)} categories")
        return f"{narrative}\n\nBreakdown:\n{listing}\n\nChart saved to: {chart_path}"

    def _goal(self, owner_id: str, message: str) -> str:
        store = UserStore(self.conn, owner_id)
        by_cat = store.spending_by_category()
        by_month = store.spending_by_month()
        if not by_cat:
            return "No spending data yet to plan against. Sync or import transactions first."

        picture = (
            "Spending by category:\n"
            + "\n".join(f"- {d['category']}: {d['total']:.2f}" for d in by_cat)
            + "\n\nRecent monthly spending:\n"
            + "\n".join(f"- {d['month']}: {d['total']:.2f}" for d in by_month)
        )
        want_frontier = "think hard" in message.lower() or "use claude" in message.lower()
        provider, _tier, note = provider_for(self.settings, want_frontier)
        plan = provider.complete(
            "The user has this goal: " + message + "\n\n"
            "Using their actual spending below, propose concrete numbered steps that reference real figures, "
            "for example which categories to trim and by how much, and roughly how long the goal would take at that rate. "
            "Be specific and realistic.\n\n" + picture,
            system="You are a careful, practical financial planning assistant.",
        )

        store.add_audit("finance_goal", message[:120])
        disclaimer = "\n\nThese suggestions are based on your own transaction data and are not professional financial advice."
        return note + plan + disclaimer
