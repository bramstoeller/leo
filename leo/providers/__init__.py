from enum import StrEnum

from leo.providers.client import ProviderClient


class EnergyProvider(StrEnum):
    FRANK_ENERGIE = "frank_energie"


def get_provider_client(provider: EnergyProvider) -> ProviderClient:
    if provider == EnergyProvider.FRANK_ENERGIE:
        from leo.providers.frank_energie.client import FrankEnergieClient

        return FrankEnergieClient()
    raise ValueError(f"Unsupported energy provider: {provider}")
