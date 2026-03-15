from pydantic import BaseModel

from leo.models.temporal import TimeResolution
from leo.prices.config import PriceProviderBrand


class PriceProviderConfig(BaseModel):
    name: str | None = None
    provider: PriceProviderBrand
    time_resolution: TimeResolution

    def __str__(self) -> str:
        return self.name or self.provider
