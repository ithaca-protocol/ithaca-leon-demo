import json
import os
import sys
import time
from datetime import datetime

from dotenv import load_dotenv
from ithaca import IthacaSDK

from models import OrderModel

sys.path.insert(0, os.getcwd())
load_dotenv()


class IthacaSocker:
    def __init__(self, sdk):
        """Class Constructor."""
        self.sdk = sdk
        self.output = print

    def run(self):
        """Attempt to establish WebSocket connection and handle reconnections if needed."""
        self.output("Attempting to connect to WebSocket...")
        self.sdk.socket.connect(on_message=self.__on_message, on_open=self.__on_open)
        while True:
            try:
                time.sleep(5)
                # self.output("WebSocket connection established successfully.")
            except Exception as e:
                self.output(
                    f"WebSocket connection error: {e}. Retrying in 5 seconds..."
                )

    def __on_open(self, ws):
        """Callback when WebSocket connection is opened."""
        self.output("WebSocket connection opened.")

    def __on_message(self, ws, message):
        """Handle incoming WebSocket messages."""
        data = json.loads(message)
        try:
            match data.get("responseType"):
                case "AUCTION_STARTED":
                    self.output(f"{datetime.now()} - 🔨 AUCTION: Started")
                case "AUCTION_FINISHED":
                    self.output(f"{datetime.now()} - 🔨 AUCTION: Finished")
                case "FUNDLOCK_UPDATED":
                    self.output(f"{datetime.now()} - 💰 FUNDLOCK: Updated")

                case "EXEC_REPORT":
                    order = OrderModel(**data.get("payload"))

                    match order.orderStatus:
                        case "CANCELED":
                            try:
                                self.output(
                                    f"{datetime.now()} - ❌ ORDER: Canceled order {order.orderId} | {order.details[0].side:<4} | {order.details[0].remainingQty:4}x {order.details[0].expiry:8} {order.details[0].contractDto.payoff:10} {order.details[0].contractDto.economics.strike:8} @ {order.netPrice:7} for {order.details[0].avgPrice:>10}"
                                )
                            except:
                                self.output(
                                    f"{datetime.now()} - ❌ ORDER: Canceled order {order.orderId}"
                                )
                        case "CANCEL_REJECTED":
                            self.output(f"{datetime.now()} - 🔴 ORDER: Cancel Rejected")
                        case "FILLED":
                            self.output(f"{datetime.now()} - ✅ ORDER: Filled")
                        case "PARTIALLY_FILLED":
                            self.output(
                                f"{datetime.now()} - 🟡 ORDER: Partially Filled"
                            )
                        case "NEW":
                            try:
                                self.output(
                                    f"{datetime.now()} - 💼 TRADE: {order.orderId} | {order.details[0].side:<4} | {order.details[0].remainingQty:4}x {order.details[0].expiry:<8} {order.details[0].contractDto.payoff:10} {order.details[0].contractDto.economics.strike:8} @ {order.netPrice:7} for {order.details[0].avgPrice:>10}"
                                )
                            except:
                                self.output(
                                    f"{datetime.now()} - 💼 TRADE: {order.orderId} | {order.details[0].side:<4} | {order.details[0].remainingQty:4}x {order.details[0].expiry:<8} {order.details[0].contractDto.payoff:10} {order.details[0].contractDto.economics.strike if order.details[0].contractDto.economics.strike else 0:8} @ {order.netPrice:7} for {order.details[0].avgPrice:>10}"
                                )

                        case "REJECTED":
                            self.output(
                                f"{datetime.now()} - ❌ ORDER: Rejected | Reason: {order.ordRejReason}"
                            )
                        case _:
                            self.output(f"{datetime.now()} - ℹ️ ORDER:")

        except Exception as e:
            self.output(f"Error processing WebSocket message: {e}")


if __name__ == "__main__":
    sdk = IthacaSDK(
        api_endpoint="https://app.canary.ithacanoemon.tech/api/v1",
        ws_endpoint="wss://app.canary.ithacanoemon.tech/wss",
        graphql_endpoint="x",
        rpc_endpoint="x",
        private_key=os.getenv("PRIVATE_KEY"),
    )

    res = sdk.auth.login()
    if not res:
        print("Connection failed, aborting")
    else:
        print("Connection successful")

        soc = IthacaSocker(sdk)
        soc.run()
