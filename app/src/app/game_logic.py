import random

from app.settings import settings


def make_spin() -> list[int]:
    return [0, 0, 0] if random.random() < 0.5 else [0, 1, 2]


def compute_multiplier(symbol_idxs: list[int]) -> float:
    if all(symbol == 0 for symbol in symbol_idxs):
        return settings.app.jackpot_multiplier
    else:
        return 0.0
