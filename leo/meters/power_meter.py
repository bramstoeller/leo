from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from leo.models.electrical import Energy, Power


class PowerMeter(ABC):
    @abstractmethod
    def fetch(self) -> None:
        pass

    @abstractmethod
    def power(self, fetch: bool = True) -> tuple[Power | None, Power | None, Power | None]:
        pass

    @abstractmethod
    def total_import(self, fetch: bool = True) -> Energy | None:
        pass

    @abstractmethod
    def total_export(self, fetch: bool = True) -> Energy | None:
        pass
