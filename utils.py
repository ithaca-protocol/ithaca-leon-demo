import os

from dotenv import load_dotenv
from ithaca import IthacaSDK

load_dotenv()


def init_sdk() -> IthacaSDK:
    sdk = IthacaSDK(
        api_endpoint="https://app.canary.ithacanoemon.tech/api/v1",
        ws_endpoint="wss://app.canary.ithacanoemon.tech/wss",
        graphql_endpoint="x",
        rpc_endpoint=os.getenv("RPC_ENDPOINT"),
        private_key=os.getenv("PRIVATE_KEY"),
    )

    print("-" * 50)
    print("Logging in to Ithaca Backend...")
    is_logged_in = sdk.auth.login()
    print(is_logged_in)
    return sdk
