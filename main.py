import json

import pandas as pd
from ithaca import IthacaSDK

from models import OrderModel
from utils import init_sdk


def get_system_info(sdk: IthacaSDK):
    print("-" * 50)
    print("Fetching system info...")
    system = sdk.protocol.system_info().get("payload")
    print(json.dumps(system, indent=4))


def get_fundlock_balances(sdk: IthacaSDK):
    print("-" * 50)
    print("Fetching fundlock state...")
    fund_lock_state = sdk.client.fundlock_state()
    print(pd.DataFrame(fund_lock_state.get("payload")))


def fetch_contracts(sdk: IthacaSDK):
    print("-" * 50)
    print("Fetching contracts for BTC...")

    contracts_df = sdk.protocol.contract_list_df()
    contracts_df = contracts_df[contracts_df["pair"] == "WBTC/USDC"]
    print(contracts_df.payoff.unique())
    print(f"Found {contracts_df.shape[0]} contracts")
    print(contracts_df[contracts_df["payoff"] == "Spot"])


def send_order(sdk: IthacaSDK, payoff, expiry, strike, price, side, quantity):
    print("-" * 50)
    print("Sending Order...")

    put_contract_id = sdk.protocol.find_contract(payoff, expiry, strike)

    legs = [(put_contract_id, side, quantity)]
    print(legs, price)

    order_response = sdk.orders.new_order(legs=legs, price=price)
    print(order_response)


def fetch_orders(sdk: IthacaSDK):
    print("-" * 50)
    print("Fetching Orders...")
    orders = sdk.orders.open_orders()
    # print(json.dumps(orders.get("payload")[0], indent=4))

    flds = [
        "orderId",
        "contractId",
        "payoff",
        "expiry",
        "strike",
        "price",
        "position",
        "unitPrice",
    ]
    orders = pd.DataFrame(
        [OrderModel(**order).detail()[0] for order in orders.get("payload", [])]
    )

    print(orders)
    # OrderModel(**orders.get("payload", [])[0])


def fetch_positions(sdk: IthacaSDK):
    print("-" * 50)
    print("Fetching Positions...")
    positions = sdk.client.current_positions()
    # print(json.dumps(positions.get("payload"), indent=4))

    # bal = sdk.fundlock.fundlock_balances()
    # print(bal)

    # sdk.fundlock.deposit("WBTC", 1)


if __name__ == "__main__":
    sdk = init_sdk()
    # get_system_info(sdk)
    fetch_contracts(sdk)

    # get_fundlock_balances(sdk)

    # side = "BUY"
    # quantity = 0.0001
    # payoff = "Put"
    # expiry = "2025-11-28"
    # strike = 88000
    # price = sdk.calc_server.get_price(payoff, expiry, strike, currency="BTC")
    # print(f"Calculated price from server: {price}")
    # price *= quantity
    # print(f"Unit price: {price}")

    # put_contract_id = sdk.protocol.find_contract(payoff, expiry, strike)

    # legs = [(put_contract_id, side, quantity)]

    # send_order(sdk, payoff, expiry, strike, price, side, quantity)

    # fetch_orders(sdk)

    # fetch_positions(sdk)
