from plaid.model.transactions_sync_request import TransactionsSyncRequest


class PlaidSource:
    source_name = "plaid"

    def __init__(self, access_token: str, client):
        self.access_token = access_token
        self.client = client

    def fetch(self) -> list[dict]:
        resp = self.client.transactions_sync(
            TransactionsSyncRequest(access_token=self.access_token)
        )
        out = []
        for t in resp.added:
            out.append({
                "external_id": t.transaction_id,
                "date": str(t.date),
                "name": t.name,
                "amount": float(t.amount),
            })
        return out
