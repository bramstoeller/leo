from leo.prices.config import PriceProviderName
from leo.prices.provider import PriceProvider


def get_price_provider(provider: PriceProviderName) -> PriceProvider:
    if provider == "frank_energie":
        from leo.prices.frank_energie.provider import FrankEnergieProvider

        return FrankEnergieProvider()

    raise ValueError(f"Unsupported energy provider: {provider}")
