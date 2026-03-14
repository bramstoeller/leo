from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class ElectricityPrice(BaseModel):
    model_config = ConfigDict(extra="ignore")

    price_from: AwareDatetime = Field(alias="from")
    price_till: AwareDatetime = Field(alias="till")
    all_in_price: float = Field(alias="allInPrice")


class MarketPrices(BaseModel):
    model_config = ConfigDict(extra="ignore")

    electricity_prices: list[ElectricityPrice] = Field(alias="electricityPrices")


class MarketPricesResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    market_prices: MarketPrices = Field(alias="marketPrices")


class Error(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: str


class GraphQLResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    data: MarketPricesResponse | None
    errors: list[Error] | None = None
