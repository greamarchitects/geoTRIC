# derivation.py
# Iterative rule application engine

from typing import List
from .symbols import Symbol
from .rules import Rule


class Derivation:

    def __init__(self, seed: List[Symbol], rules: List[Rule]):
        self.seed = seed
        self.rules = rules

    def step(self, symbols: List[Symbol], step_index: int) -> List[Symbol]:
        result = []
        for sym in symbols:
            applied = False
            for rule in self.rules:
                if rule.applies_to(sym):
                    result.extend(rule.apply(sym, step_index))
                    applied = True
                    break
            if not applied:
                result.append(sym)
        return result

    def run(self, steps: int):
        history = [self.seed]
        current = self.seed
        for i in range(steps):
            current = self.step(current, i)
            history.append(current)
        return history