"""Gochar (transit) scoring — pure math, consumes planet positions."""

from __future__ import annotations

from clawclaw_soul.tables import (
    GOCHAR_FAVORABLE,
    VEDHA_PAIRS,
    get_house_from_moon,
)


def score_transit(
    planet: str,
    house_from_moon: int,
    is_favorable: bool,
    vedha_cancelled: bool,
) -> float:
    """Score a single planet's transit position.

    Args:
        planet: Planet name
        house_from_moon: House number (1-12) from natal Moon
        is_favorable: Whether this house is favorable for this planet
        vedha_cancelled: Whether a vedha obstruction cancels the benefit

    Returns:
        Score in range [-1, +1]
    """
    if is_favorable:
        if vedha_cancelled:
            return 0.0  # Vedha cancels favorable effect
        # Favorable houses get positive score, scaled by house importance
        # Houses 1, 5, 9 (trikona) and 10, 11 (upachaya) are strongest
        strong_houses = {1, 5, 9, 10, 11}
        if house_from_moon in strong_houses:
            return 0.8
        return 0.5
    else:
        # Unfavorable houses get negative score
        # Houses 6, 8, 12 (dusthana) are worst
        dusthana = {6, 8, 12}
        if house_from_moon in dusthana:
            return -0.7
        return -0.3


def check_vedha(
    planet: str,
    house_from_moon: int,
    all_transit_houses: dict[str, int],
) -> bool:
    """Check if a planet's favorable transit is cancelled by vedha.

    Args:
        planet: The planet whose transit we're checking
        house_from_moon: Its house from Moon
        all_transit_houses: Dict of {planet: house_from_moon} for all transiting planets

    Returns:
        True if vedha cancels the favorable transit
    """
    vedha_map = VEDHA_PAIRS.get(planet, {})
    obstructing_house = vedha_map.get(house_from_moon)

    if obstructing_house is None:
        return False

    # Check if any OTHER planet occupies the obstructing house
    for other_planet, other_house in all_transit_houses.items():
        if other_planet != planet and other_house == obstructing_house:
            return True

    return False


def compute_transit_scores(
    current_positions: dict[str, dict],
    natal_moon_sign: str,
) -> dict[str, float]:
    """Compute transit (gochar) scores for all planets.

    Args:
        current_positions: Current planet positions from ephemeris
        natal_moon_sign: The natal Moon's sign name

    Returns:
        Dict of {planet: score} where score is in [-1, +1]
    """
    # First pass: compute house from moon for each planet
    transit_houses: dict[str, int] = {}
    for planet, pos in current_positions.items():
        house = get_house_from_moon(pos["sign"], natal_moon_sign)
        transit_houses[planet] = house

    # Second pass: compute scores with vedha checking
    scores: dict[str, float] = {}
    for planet, house in transit_houses.items():
        favorable_houses = GOCHAR_FAVORABLE.get(planet, [])
        is_favorable = house in favorable_houses
        vedha_cancelled = False

        if is_favorable:
            vedha_cancelled = check_vedha(planet, house, transit_houses)

        scores[planet] = score_transit(planet, house, is_favorable, vedha_cancelled)

    return scores
