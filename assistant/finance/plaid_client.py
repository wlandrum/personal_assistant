import os
import plaid
from plaid.api import plaid_api

ENVS = {
    "sandbox": plaid.Environment.Sandbox,
    "production": plaid.Environment.Production,
}


def build_plaid_client(plaid_env: str):
    config = plaid.Configuration(
        host=ENVS[plaid_env],
        api_key={"clientId": os.environ["PLAID_CLIENT_ID"], "secret": os.environ["PLAID_SECRET"]},
    )
    return plaid_api.PlaidApi(plaid.ApiClient(config))
