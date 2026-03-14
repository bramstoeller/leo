from pydantic import AwareDatetime, BaseModel, Field


class ElectricityPrice(BaseModel):
    price_from: AwareDatetime = Field(alias="from")
    price_till: AwareDatetime = Field(alias="till")
    all_in_price: float = Field(alias="allInPrice")

    class Meta:
        ignore_extra = True


class MarketPrices(BaseModel):
    electricity_prices: list[ElectricityPrice] = Field(alias="electricityPrices")

    class Meta:
        ignore_extra = True


class MarketPricesResponse(BaseModel):
    market_prices: MarketPrices = Field(alias="marketPrices")

    class Meta:
        ignore_extra = True


class Error(BaseModel):
    message: str

    class Meta:
        ignore_extra = True


class GraphQLResponse(BaseModel):
    data: MarketPricesResponse | None
    errors: list[Error] | None = None

    class Meta:
        ignore_extra = True
