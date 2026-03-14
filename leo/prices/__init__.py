from typing import Literal

from leo.prices.provider import PriceProvider

EnergyProvider = Literal["frank_energie"]


def get_price_provider(provider: EnergyProvider) -> PriceProvider:
    if provider == "frank_energie":
        from leo.prices.frank_energie.provider import FrankEnergieProvider

        return FrankEnergieProvider()

    raise ValueError(f"Unsupported energy provider: {provider}")
