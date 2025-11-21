from datetime import datetime

import pandas as pd
from rich.console import Console
from rich.table import Table

from utils import init_sdk

sdk = init_sdk()

# res = sdk.auth.login()

contracts_data = sdk.protocol.contract_list().get("payload")

contracts = [
    {
        **row,
        "strike": row["economics"].get("strike"),
        "expiry": row["economics"]["expiry"],
    }
    for row in contracts_data
    if row["economics"]["qtyCurrency"] == "WBTC"
]
contracts = pd.DataFrame(contracts)
strikes = contracts["strike"].unique().tolist()[1:]
expiries = contracts["expiry"].unique().tolist()

prices = sdk.analytics.best_prices_precise().get("payload")

for expiry in sorted(expiries):
    if expiry != 251226080:
        continue
    table = Table(title=f"Expiry: {expiry}")
    table.add_column("ID", justify="right", style="magenta")
    table.add_column("Call Bid", justify="right", style="cyan", no_wrap=True)
    table.add_column("Call Model", justify="right", style="cyan", no_wrap=True)
    table.add_column("Call Ask", justify="right", style="cyan", no_wrap=True)
    table.add_column("Strike", justify="right", style="cyan", no_wrap=True)
    table.add_column("Put Bid", justify="right", style="cyan", no_wrap=True)
    table.add_column("Put Model", justify="right", style="cyan", no_wrap=True)
    table.add_column("Put Ask", justify="right", style="cyan", no_wrap=True)
    table.add_column("ID", justify="right", style="magenta")
    for strike in sorted(strikes):
        call_row = contracts[
            (contracts["strike"] == strike)
            & (contracts["expiry"] == expiry)
            & (contracts["payoff"] == "Call")
        ]
        call_id = str(call_row.contractId.values[0]) if not call_row.empty else ""
        call_price = prices.get(call_id) if not call_row.empty else None
        call_model = sdk.calc_server.get_price(
            "Call", datetime.strptime(str(expiry), "%y%m%d%H%M").date(), strike, "BTC"
        )
        put_row = contracts[
            (contracts["strike"] == strike)
            & (contracts["expiry"] == expiry)
            & (contracts["payoff"] == "Put")
        ]
        put_id = str(put_row.contractId.values[0]) if not put_row.empty else ""
        put_price = prices.get(put_id) if not put_row.empty else None
        put_model = sdk.calc_server.get_price(
            "Put", datetime.strptime(str(expiry), "%y%m%d%H%M").date(), strike, "BTC"
        )

        table.add_row(
            str(call_row.contractId.values[0] if not call_row.empty else ""),
            str(call_price.get("bestBid", "") if call_price else ""),
            f"{call_model:.2f}" if call_model else "",
            str(call_price.get("bestAsk", "") if call_price else ""),
            str(strike),
            str(put_price.get("bestBid", "") if put_price else ""),
            f"{put_model:.2f}" if put_model else "",
            str(put_price.get("bestAsk", "") if put_price else ""),
            str(put_row.contractId.values[0] if not put_row.empty else ""),
        )
    console = Console()
    console.print(table)
