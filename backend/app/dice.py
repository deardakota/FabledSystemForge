"""
Core dice engine for the Story Telling App.

Supports polyhedral dice: d4, d6, d8, d10, d12, d20, and d100 (percentile).
The only rigid mechanic is the use of dice for player interactions.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Literal

# Valid polyhedral dice sizes supported by this app.
_DICE_SIZES = frozenset({4, 6, 8, 10, 12, 20, 100})


class DiceError(ValueError):
    """Raised when an invalid die size or roll specification is provided."""


@dataclass(frozen=True)
class Die:
    """A single polyhedral die with a given number of sides."""

    sides: int

    def __post_init__(self) -> None:
        if self.sides not in _DICE_SIZES:
            raise DiceError(
                f"Unsupported die size: {self.sides}. "
                f"Supported sizes: {sorted(_DICE_SIZES)}"
            )

    def roll(self) -> int:
        """Roll the die once, returning a value in [1, sides]."""
        return random.randint(1, self.sides)


@dataclass(frozen=True)
class DiceRoll:
    """Result of rolling one or more dice."""

    dice: tuple[Die, ...]
    results: tuple[int, ...]
    total: int

    @property
    def individual(self) -> list[int]:
        return list(self.results)


def roll_dice(*dice_sizes: int, seed: int | None = None) -> DiceRoll:
    """
    Roll one or more polyhedral dice.

    Parameters
    ----------
    *dice_sizes:
        Sides of each die to roll (e.g. 20 for d20, 10 for d10).
    seed:
        Optional seed for reproducible rolls (testing/debugging).

    Returns
    -------
    DiceRoll
        The individual results and their total.
    """
    if not dice_sizes:
        raise DiceError("At least one die must be rolled.")

    if seed is not None:
        random.seed(seed)

    dice = tuple(Die(sides) for sides in dice_sizes)
    results = tuple(d.roll() for d in dice)
    return DiceRoll(dice=dice, results=results, total=sum(results))


def roll_d20(seed: int | None = None) -> DiceRoll:
    """Roll a single d20."""
    return roll_dice(20, seed=seed)


def roll_d10(seed: int | None = None) -> DiceRoll:
    """Roll a single d10."""
    return roll_dice(10, seed=seed)


def roll_percentile(seed: int | None = None) -> DiceRoll:
    """Roll a d100 (percentile die)."""
    return roll_dice(100, seed=seed)


def roll_with_advantage(dice_sizes: tuple[int, ...], seed: int | None = None) -> DiceRoll:
    """
    Roll with advantage: roll each die twice and take the higher result.

    Parameters
    ----------
    dice_sizes:
        Sides of each die to roll.
    seed:
        Optional seed for reproducible rolls.
    """
    if seed is not None:
        random.seed(seed)

    all_results: list[int] = []
    dice: list[Die] = []
    for sides in dice_sizes:
        d = Die(sides)
        dice.append(d)
        r1 = d.roll()
        r2 = d.roll()
        all_results.append(max(r1, r2))

    return DiceRoll(
        dice=tuple(dice),
        results=tuple(all_results),
        total=sum(all_results),
    )


def roll_with_disadvantage(dice_sizes: tuple[int, ...], seed: int | None = None) -> DiceRoll:
    """
    Roll with disadvantage: roll each die twice and take the lower result.

    Parameters
    ----------
    dice_sizes:
        Sides of each die to roll.
    seed:
        Optional seed for reproducible rolls.
    """
    if seed is not None:
        random.seed(seed)

    all_results: list[int] = []
    dice: list[Die] = []
    for sides in dice_sizes:
        d = Die(sides)
        dice.append(d)
        r1 = d.roll()
        r2 = d.roll()
        all_results.append(min(r1, r2))

    return DiceRoll(
        dice=tuple(dice),
        results=tuple(all_results),
        total=sum(all_results),
    )


def compare_to_target(total: int, target: int) -> Literal["success", "failure", "critical"]:
    """
    Compare a dice roll total to a target number.

    Returns
    -------
    "success"
        The total meets or exceeds the target.
    "failure"
        The total is below the target.
    "critical"
        The total is a natural 20 (for d20) or natural 100 (for d100).
    """
    if total == 20:
        return "critical"
    if total >= target:
        return "success"
    return "failure"
