import csv
import time
from datetime import datetime, timedelta, timezone

from utils import init_sdk

sdk = init_sdk()


SPOT_SPREAD = 2
OPTION_SPREAD_BPS = 2_000  # 10 bps
GTD_MINUTES = 3
ORDER_QTY = 0.0001
NUM_STRIKE = 6


def run():
    res = sdk.auth.login()
    print(f"==== Authenticating: {res} ====")
    order_details = []

    try:
        sdk.orders.order_cancel_all()

        contracts = sdk.protocol.contract_list()
        contracts = list(
            filter(
                lambda x: x["economics"]["qtyCurrency"] == "WBTC",
                contracts.get("payload", []),
            )
        )

        expiries = {contract["economics"]["expiry"] for contract in contracts}
        print("Contract expiries:", sorted(expiries))

        spot = sdk.calc_server.get_price("Spot", "2025-10-17", 0, "BTC")
        print("Spot prices:", spot)
        OPTION_SPREAD = spot / OPTION_SPREAD_BPS / 2

        # NAF
        naf_unit_price = spot - SPOT_SPREAD
        naf_bid = round(ORDER_QTY * naf_unit_price, 4)
        sdk.orders.new_order(
            legs=[(87633, "BUY", ORDER_QTY)],
            price=naf_bid,
        )
        order_details.append(
            (87633, "NAF", "N/A", "N/A", "BID", naf_bid, naf_unit_price)
        )
        naf_unit_price = spot + SPOT_SPREAD
        naf_ask = round(-naf_unit_price * ORDER_QTY, 4)
        sdk.orders.new_order(
            legs=[(87633, "SELL", ORDER_QTY)],
            price=naf_ask,
        )
        order_details.append(
            (87633, "NAF", "N/A", "N/A", "ASK", naf_ask, naf_unit_price)
        )
        # print("NAF Bid/ASK", naf_bid, naf_ask)

        # Forwards

        forward_contracts = [c for c in contracts if c["payoff"] == "Forward"]
        for contract in forward_contracts:
            contract_id = contract.get("contractId")
            expiry = contract["economics"]["expiry"]
            fwd_unit_price = spot - SPOT_SPREAD
            fwd_bid = round(ORDER_QTY * fwd_unit_price, 4)
            sdk.orders.new_order(
                legs=[(contract_id, "BUY", ORDER_QTY)],
                price=fwd_bid,
            )
            order_details.append(
                (contract_id, "Forward", expiry, "N/A", "BID", fwd_bid, fwd_unit_price)
            )
            fwd_unit_price = spot + SPOT_SPREAD
            fwd_ask = round(-fwd_unit_price * ORDER_QTY, 4)
            sdk.orders.new_order(
                legs=[(contract_id, "SELL", ORDER_QTY)],
                price=fwd_ask,
            )
            order_details.append(
                (contract_id, "Forward", expiry, "N/A", "ASK", fwd_ask, fwd_unit_price)
            )
            # print(f"FWD {expiry} Bid/ASK", fwd_bid, fwd_ask)

        # Options
        contracts = [
            c
            for c in contracts
            if c["payoff"] in ["Call", "Put", "BinaryCall", "BinaryPut"]
        ]
        positions = [
            {
                "contractId": contract["contractId"],
                "payoff": contract["payoff"],
                "strike": contract["economics"]["strike"],
                "expiry": datetime.strptime(
                    str(contract["economics"]["expiry"]), "%y%m%d%H%M"
                ).strftime("%Y-%m-%d"),
            }
            for contract in contracts
        ]

        prices = sdk.calc_server.mark_price(positions=positions, currency="BTC")
        prices_map = {row["contractId"]: row["price"] for row in prices}

        order_expiry = datetime.now(tz=timezone.utc) + timedelta(minutes=GTD_MINUTES)
        tif = int(order_expiry.timestamp() * 1000)

        orders_to_send = []

        for contract in contracts:
            contract_id = contract.get("contractId")
            expiry = contract["economics"]["expiry"]
            if expiry != 251226080:
                continue

            strike = contract["economics"]["strike"]
            payoff = contract["payoff"]
            if (
                payoff in ["Call", "BinaryCall"]
                and strike < spot
                and strike > spot + NUM_STRIKE * 500
            ):
                continue
            if (
                payoff in ["Put", "BinaryPut"]
                and strike > spot
                and strike < spot - NUM_STRIKE * 500
            ):
                continue

            mid = prices_map.get(contract_id)
            # print(f"{contract_id} {payoff} {expiry} {strike}, mid: {mid}")

            # BID
            legs = [(contract_id, "BUY", ORDER_QTY)]
            unit_price = mid - OPTION_SPREAD
            price = round(unit_price * ORDER_QTY, 4)
            # res = sdk.orders.new_order(legs=legs, price=price)
            orders_to_send.append((legs, price, "GOOD_TILL_DATE", f"Quoter - {payoff}"))
            order_details.append(
                (contract_id, payoff, expiry, strike, "BID", price, unit_price)
            )

            # ASK
            legs = [(contract_id, "SELL", ORDER_QTY)]
            unit_price = mid + OPTION_SPREAD
            price = round(-unit_price * ORDER_QTY, 4)
            # res = sdk.orders.new_order(legs=legs, price=price)
            orders_to_send.append((legs, price, "GOOD_TILL_DATE", f"Quoter - {payoff}"))
            order_details.append(
                (contract_id, payoff, expiry, strike, "ASK", price, unit_price)
            )
        print(f"Sending {len(orders_to_send)} orders...")
        res = sdk.orders.new_orders(orders=orders_to_send, tif=tif)
        errors = {key: val for key, val in res.get("payload").items() if val != "OK"}
        print(errors)

        with open("orders.csv", mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "contractId",
                    "payoff",
                    "expiry",
                    "strike",
                    "side",
                    "price",
                    "unit_price",
                ]
            )
            writer.writerows(order_details)
    except Exception as e:
        print(f"Error: {e}")
        return


if __name__ == "__main__":
    while True:
        try:
            run()
        except Exception as e:
            print(f"Fatal error: {e}")
        time.sleep(3)
