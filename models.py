from datetime import datetime, timedelta
from typing import List, Literal, Optional

from pydantic import BaseModel


class Economics(BaseModel):
    currencyPair: str
    expiry: int
    strike: Optional[float] = None
    priceCurrency: str
    qtyCurrency: str


class ContractDto(BaseModel):
    contractId: int
    payoff: str
    economics: Economics
    tradeable: bool


class Detail(BaseModel):
    contractId: int
    contractDto: ContractDto
    side: Literal["SELL", "BUY"]
    originalQty: float
    remainingQty: float
    thisFillQty: Optional[float] = 0
    cancelledQty: float
    avgPrice: float
    totalCost: float
    currencyPair: str
    expiry: int

    def position(self):
        payoff = (
            "Forward" if self.contractDto.payoff == "Spot" else self.contractDto.payoff
        )
        expiry = datetime.strptime(str(self.expiry), "%y%m%d%H%M")
        if self.contractDto.payoff == "Spot":
            expiry = datetime.now() + timedelta(days=1)

        return {
            "contractId": self.contractId,
            "payoff": payoff,
            "expiry": expiry.strftime("%Y-%m-%d"),
            "strike": self.contractDto.economics.strike or 0,
            "position": self.thisFillQty,
            "price": self.avgPrice,
        }

    def detail(self):
        payoff = (
            "Forward" if self.contractDto.payoff == "Spot" else self.contractDto.payoff
        )
        expiry = datetime.strptime(str(self.expiry), "%y%m%d%H%M")
        if self.contractDto.payoff == "Spot":
            expiry = datetime.now() + timedelta(days=1)

        return {
            "contractId": self.contractId,
            "payoff": payoff,
            "expiry": expiry.strftime("%Y-%m-%d"),
            "strike": self.contractDto.economics.strike or 0,
            "position": self.thisFillQty * (1 if self.side == "BUY" else -1)
            if self
            else 0,
            "price": self.avgPrice,
        }


class OrderModel(BaseModel):
    revDate: int
    orderId: int
    clientId: int
    orderStatus: Literal[
        "NEW", "FILLED", "CANCELED", "PENDING", "REJECTED"
    ]  # extend as needed
    ordRejReason: Optional[str] = None
    netPrice: float
    orderGenesis: str
    orderDescr: str
    timeInForce: str
    orderClass: str
    requestSinglePrice: bool
    iocAuctionTime: int
    details: List[Detail]
    totalOpenOrdersCount: Optional[int] = None
    insertionDate: int
    spotPriceAtCreation: float

    @property
    def rev_date_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.revDate / 1000)

    @property
    def insertion_date_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.insertionDate / 1000)

    def position(self):
        return [detail.position() for detail in self.details]

    def detail(self):
        data = [
            {
                "orderId": self.orderId,
                "revDate": self.revDate,
                **detail.detail(),
                "price": self.netPrice,
                "spotPriceAtCreation": self.spotPriceAtCreation,
            }
            for detail in self.details
        ]

        return [
            {
                **row,
                "unitPrice": self.netPrice / row.get("position")
                if row.get("position") != 0
                else 0,
            }
            for row in data
        ]
