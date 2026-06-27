from assistant.data.store import UserStore
from assistant.config import Settings
from assistant.finance.plaid_client import build_plaid_client
from assistant.finance.plaid_source import PlaidSource
from assistant.finance.categorize import categorize


class FinanceSubagent:
    name = "finance"

    def __init__(self, conn, settings: Settings, embedder=None):
        self.conn = conn
        self.settings = settings

    def handle(self, owner_id: str, message: str) -> str:
        token = UserStore(self.conn, owner_id).get_credential("plaid")
        if not token:
            return "No bank connection found. Run connect_plaid for sandbox, or import a CSV with import_csv."
        client = build_plaid_client(self.settings.finance.plaid_env)
        source = PlaidSource(token, client)
        return self._ingest(owner_id, source)

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
