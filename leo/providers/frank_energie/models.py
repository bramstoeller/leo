"""Pydantic models for Frank Energie GraphQL API responses.

API endpoint: POST https://graphql.frankenergie.nl/
Query: MarketPrices(date, resolution) → marketPrices.electricityPrices[]
"""

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class ElectricityPrice(BaseModel):
    """Single electricity price entry from the marketPrices query."""

    model_config = ConfigDict(populate_by_name=True)

    price_from: AwareDatetime = Field(alias="from")
    price_till: AwareDatetime = Field(alias="till")
    all_in_price: float = Field(alias="allInPrice")


class MarketPrices(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    electricity_prices: list[ElectricityPrice] = Field(alias="electricityPrices")


class MarketPricesResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    market_prices: MarketPrices = Field(alias="marketPrices")


class GraphQLResponse(BaseModel):
    data: MarketPricesResponse | None = None
