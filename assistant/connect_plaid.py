import sys
from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.products import Products
from assistant.config import load_settings
from assistant.finance.plaid_client import build_plaid_client
from assistant.data.db import connect
from assistant.data.store import UserStore


def main():
    owner_id = sys.argv[1] if len(sys.argv) > 1 else None
    if not owner_id:
        print("usage: python -m assistant.connect_plaid <owner_id>")
        return
    settings = load_settings()
    client = build_plaid_client(settings.finance.plaid_env)

    pt = client.sandbox_public_token_create(
        SandboxPublicTokenCreateRequest(
            institution_id="ins_109508",
            initial_products=[Products("transactions")],
        )
    ).public_token

    access_token = client.item_public_token_exchange(
        ItemPublicTokenExchangeRequest(public_token=pt)
    ).access_token

    conn = connect()
    UserStore(conn, owner_id).save_credential("plaid", access_token)
    print(f"Stored Plaid sandbox access token for owner {owner_id}.")


if __name__ == "__main__":
    main()
