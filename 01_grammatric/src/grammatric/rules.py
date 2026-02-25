# rules.py
# Minimal grammar rule abstraction

from dataclasses import dataclass
from typing import Callable, List
from .symbols import Symbol


@dataclass
class Rule:
    target: str
    replacement: Callable[[Symbol, int], List[Symbol]]

    def applies_to(self, symbol: Symbol) -> bool:
        return symbol.name == self.target

    def apply(self, symbol: Symbol, step_index: int) -> List[Symbol]:
        return self.replacement(symbol, step_index)