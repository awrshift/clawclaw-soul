"""Classical Vedic yoga detection — adapted from Jyotish engine.

Detects ~58 planetary combinations (yogas) from natal chart data.
Copy + Adapt architecture: full decoupling from Jyotish.
"""

from __future__ import annotations

from clawclaw_soul.tables import (
    COMBUSTION_ORBS,
    COMBUSTION_ORBS_RETROGRADE,
    DEBILITATION_SIGN,
    DUSTHANA_HOUSES,
    EXALTATION_SIGN,
    KENDRA_HOUSES,
    NATURAL_BENEFICS,
    NATURAL_FRIENDSHIPS,
    NATURAL_MALEFICS,
    OWNERSHIP,
    SIGN_LORDS,
    SIGNS,
    SPECIAL_ASPECTS,
    TRIKONA_HOUSES,
    get_dignity,
)

# Aliases for compatibility with Jyotish detector code
EXALTATION = EXALTATION_SIGN
DEBILITATION = DEBILITATION_SIGN
BENEFICS = NATURAL_BENEFICS
MALEFICS = NATURAL_MALEFICS


# ──────────────────────────────────────────────
# Data Adapter: ClawClaw Soul → Jyotish format
# ──────────────────────────────────────────────

def _adapt_chart_data(
    positions: dict[str, dict],
    houses: list[dict],
    combustion: dict[str, bool],
) -> list[dict]:
    """Convert ClawClaw Soul data format to Jyotish-compatible planet list.

    Jyotish detectors expect list[dict] with keys:
    name, house, sign, degree, longitude, dignity, motion.
    """
    planet_house_map: dict[str, int] = {}
    for h in houses:
        for p in h["planets"]:
            planet_house_map[p] = h["number"]

    planets = []
    for name, pos in positions.items():
        dignity = get_dignity(name, pos["sign"], pos["degree"])
        planets.append({
            "name": name,
            "house": planet_house_map.get(name, 0),
            "sign": pos["sign"],
            "degree": pos["degree"],
            "longitude": pos["lon"],
            "dignity": dignity,
            "motion": "retrograde" if pos.get("retrograde") else "direct",
        })
    return planets


# ──────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────

def _houses_from(base_house: int, offset: int) -> int:
    """Calculate house number at offset from base (1-indexed, wrapping)."""
    return (base_house - 1 + offset) % 12 + 1


def _planet_house(planets: list[dict], name: str) -> int:
    for p in planets:
        if p["name"] == name:
            return p["house"]
    return 0


def _planet_sign(planets: list[dict], name: str) -> str:
    for p in planets:
        if p["name"] == name:
            return p["sign"]
    return ""


def _planet_dignity(planets: list[dict], name: str) -> str:
    for p in planets:
        if p["name"] == name:
            return p.get("dignity", "")
    return ""


def _planet_longitude(planets: list[dict], name: str) -> float | None:
    for p in planets:
        if p["name"] == name:
            return p.get("longitude")
    return None


def _house_lord(houses: list[dict], house_num: int) -> str:
    for h in houses:
        if h["number"] == house_num:
            return h["lord"]
    return ""


def _planets_in_house(planets: list[dict], house_num: int) -> list[str]:
    return [p["name"] for p in planets if p["house"] == house_num]


def _is_aspected_by(target_house: int, observer: str, planets: list[dict]) -> bool:
    """Check if target_house receives Graha Drishti from observer planet."""
    obs_house = _planet_house(planets, observer)
    if not obs_house or not target_house:
        return False
    if _houses_from(obs_house, 6) == target_house:
        return True
    for offset in SPECIAL_ASPECTS.get(observer, []):
        if _houses_from(obs_house, offset - 1) == target_house:
            return True
    return False


# ──────────────────────────────────────────────
# Yoga Detectors
# ──────────────────────────────────────────────

def _pancha_mahapurusha(planets: list[dict]) -> list[dict]:
    """5 Mahapurusha Yogas: Mars/Mercury/Jupiter/Venus/Saturn
    in own sign or exalted, AND in a kendra house."""
    configs = {
        "Mars": ("Ruchaka Yoga", "Courage, leadership, military prowess, physical strength"),
        "Mercury": ("Bhadra Yoga", "Intelligence, eloquence, business acumen, learning"),
        "Jupiter": ("Hamsa Yoga", "Wisdom, spirituality, respect, teaching ability"),
        "Venus": ("Malavya Yoga", "Luxury, arts, beauty, material comforts, relationships"),
        "Saturn": ("Shasha Yoga", "Authority, discipline, organizational power, longevity"),
    }
    yogas = []
    for p in planets:
        name = p["name"]
        if name not in configs:
            continue
        sign = p["sign"]
        house = p["house"]
        is_own = sign in OWNERSHIP.get(name, [])
        is_exalted = sign == EXALTATION.get(name)
        if (is_own or is_exalted) and house in KENDRA_HOUSES:
            yoga_name, desc = configs[name]
            strength = "exalted" if is_exalted else "own sign"
            yogas.append({
                "name": yoga_name,
                "type": "auspicious",
                "category": "Mahapurusha",
                "planets": [name],
                "description": f"{name} in {sign} ({strength}) in house {house} (kendra). {desc}.",
            })
    return yogas


def _raja_yogas(planets: list[dict], houses: list[dict]) -> list[dict]:
    """Raja Yogas: lords of kendras and trikonas connected."""
    yogas = []
    kendra_lords: dict[str, list[int]] = {}
    trikona_lords: dict[str, list[int]] = {}
    for h_num in KENDRA_HOUSES:
        lord = _house_lord(houses, h_num)
        if lord:
            kendra_lords.setdefault(lord, []).append(h_num)
    for h_num in TRIKONA_HOUSES:
        lord = _house_lord(houses, h_num)
        if lord:
            trikona_lords.setdefault(lord, []).append(h_num)

    for planet in set(kendra_lords) & set(trikona_lords):
        k_houses = [h for h in kendra_lords[planet] if h != 1]
        t_houses = [h for h in trikona_lords[planet] if h != 1]
        if k_houses and t_houses:
            yogas.append({
                "name": "Yoga Karaka",
                "type": "auspicious",
                "category": "Raja",
                "planets": [planet],
                "description": (
                    f"{planet} lords kendra(s) {k_houses} and trikona(s) {t_houses}. "
                    f"Natural benefactor — its periods bring success and recognition."
                ),
            })

    seen: set[tuple[str, ...]] = set()
    for kl, k_nums in kendra_lords.items():
        for tl, t_nums in trikona_lords.items():
            if kl == tl:
                continue
            kl_house = _planet_house(planets, kl)
            tl_house = _planet_house(planets, tl)
            if kl_house == tl_house and kl_house > 0:
                pair = tuple(sorted([kl, tl]))
                if pair in seen:
                    continue
                seen.add(pair)
                k_real = [h for h in k_nums if h != 1]
                t_real = [h for h in t_nums if h != 1]
                if not k_real and not t_real:
                    continue
                yogas.append({
                    "name": "Raja Yoga",
                    "type": "auspicious",
                    "category": "Raja",
                    "planets": list(pair),
                    "description": (
                        f"{kl} (lord of kendra {k_nums}) conjunct {tl} "
                        f"(lord of trikona {t_nums}) in house {kl_house}. "
                        f"Power, status, and achievement."
                    ),
                })

    for tl, t_nums in trikona_lords.items():
        t_real = [h for h in t_nums if h != 1]
        if not t_real:
            continue
        tl_house = _planet_house(planets, tl)
        if tl_house in KENDRA_HOUSES:
            already = any(
                tl in y["planets"] and y["name"] in ("Raja Yoga", "Yoga Karaka")
                for y in yogas
            )
            if not already:
                yogas.append({
                    "name": "Raja Yoga",
                    "type": "auspicious",
                    "category": "Raja",
                    "planets": [tl],
                    "description": (
                        f"{tl} (lord of trikona {t_real}) placed in "
                        f"kendra house {tl_house}. Fortune supports career and public life."
                    ),
                })

    return yogas


def _gajakesari(planets: list[dict]) -> list[dict]:
    """Gajakesari Yoga: Jupiter in kendra from Moon."""
    moon_house = _planet_house(planets, "Moon")
    jup_house = _planet_house(planets, "Jupiter")
    if not moon_house or not jup_house:
        return []

    kendras_from_moon = {
        _houses_from(moon_house, 0),
        _houses_from(moon_house, 3),
        _houses_from(moon_house, 6),
        _houses_from(moon_house, 9),
    }
    if jup_house not in kendras_from_moon:
        return []

    malefic_with_jup = [
        p["name"] for p in planets
        if p["house"] == jup_house and p["name"] in MALEFICS
    ]
    malefic_with_moon = [
        p["name"] for p in planets
        if p["house"] == moon_house and p["name"] in MALEFICS
    ]
    if malefic_with_jup or malefic_with_moon:
        spoilers = malefic_with_jup + malefic_with_moon
        return [{
            "name": "Gajakesari Yoga (weakened)",
            "type": "auspicious",
            "category": "Benefic",
            "planets": ["Jupiter", "Moon"],
            "description": (
                f"Jupiter in house {jup_house}, kendra from Moon in house {moon_house}. "
                f"However, malefic conjunction ({', '.join(spoilers)}) weakens this yoga. "
                f"Partial benefits — reduced fame and fortune."
            ),
        }]

    return [{
        "name": "Gajakesari Yoga",
        "type": "auspicious",
        "category": "Benefic",
        "planets": ["Jupiter", "Moon"],
        "description": (
            f"Jupiter in house {jup_house}, kendra from Moon in house {moon_house}. "
            f"Wisdom, fame, lasting reputation, and good fortune."
        ),
    }]


def _budhaditya(planets: list[dict]) -> list[dict]:
    """Budhaditya Yoga: Sun and Mercury in the same house."""
    sun_h = _planet_house(planets, "Sun")
    mer_h = _planet_house(planets, "Mercury")
    if sun_h != mer_h or sun_h == 0:
        return []

    sign = _planet_sign(planets, "Mercury")
    sign_lord = SIGN_LORDS.get(sign, "")
    mer_owns = sign in OWNERSHIP.get("Mercury", [])
    mer_exalted = sign == EXALTATION.get("Mercury")
    mer_friendly = NATURAL_FRIENDSHIPS.get("Mercury", {}).get(sign_lord) == "friend"

    if not (mer_owns or mer_exalted or mer_friendly):
        return []

    sun_lon = _planet_longitude(planets, "Sun")
    mer_lon = _planet_longitude(planets, "Mercury")
    mer_retro = any(p["name"] == "Mercury" and p.get("motion") == "retrograde" for p in planets)
    if sun_lon is not None and mer_lon is not None:
        diff = abs(sun_lon - mer_lon)
        if diff > 180:
            diff = 360 - diff
        orb = COMBUSTION_ORBS_RETROGRADE.get("Mercury", 14.0) if mer_retro else COMBUSTION_ORBS.get("Mercury", 14.0)
        if diff <= orb:
            return []

    return [{
        "name": "Budhaditya Yoga",
        "type": "auspicious",
        "category": "Benefic",
        "planets": ["Sun", "Mercury"],
        "description": (
            f"Sun and Mercury conjunct in house {sun_h} ({sign}). "
            f"Mercury has dignity here — intelligence, analytical mind, communication skills."
        ),
    }]


def _chandra_mangala(planets: list[dict]) -> list[dict]:
    """Chandra-Mangala Yoga: Moon and Mars in the same house."""
    moon_h = _planet_house(planets, "Moon")
    mars_h = _planet_house(planets, "Mars")
    if moon_h == mars_h and moon_h > 0:
        return [{
            "name": "Chandra-Mangala Yoga",
            "type": "auspicious",
            "category": "Dhana",
            "planets": ["Moon", "Mars"],
            "description": (
                f"Moon and Mars conjunct in house {moon_h}. "
                f"Wealth through bold action, entrepreneurial drive, courage."
            ),
        }]
    return []


def _amala(planets: list[dict]) -> list[dict]:
    """Amala Yoga: natural benefic in 10th house from Lagna."""
    benefics_in_10 = [
        p["name"] for p in planets
        if p["house"] == 10 and p["name"] in BENEFICS
    ]
    if benefics_in_10:
        return [{
            "name": "Amala Yoga",
            "type": "auspicious",
            "category": "Benefic",
            "planets": benefics_in_10,
            "description": (
                f"{', '.join(benefics_in_10)} in 10th house. "
                f"Virtuous reputation, ethical career, respect from society."
            ),
        }]
    return []


def _dhana_yogas(planets: list[dict], houses: list[dict]) -> list[dict]:
    """Dhana Yogas: wealth combinations involving lords of 2, 5, 9, 11."""
    yogas = []
    wealth_houses = [2, 5, 9, 11]

    lord_map: dict[str, list[int]] = {}
    for h_num in wealth_houses:
        lord = _house_lord(houses, h_num)
        if lord:
            lord_map.setdefault(lord, []).append(h_num)

    for lord, h_nums in lord_map.items():
        if len(h_nums) >= 2:
            yogas.append({
                "name": "Dhana Yoga",
                "type": "auspicious",
                "category": "Dhana",
                "planets": [lord],
                "description": (
                    f"{lord} lords wealth houses {h_nums}. "
                    f"Strong wealth potential through {lord}'s significations."
                ),
            })

    lord_2 = _house_lord(houses, 2)
    lord_11 = _house_lord(houses, 11)
    if lord_2 and lord_11 and lord_2 != lord_11:
        h2l = _planet_house(planets, lord_2)
        h11l = _planet_house(planets, lord_11)
        if h2l == h11l and h2l > 0:
            yogas.append({
                "name": "Dhana Yoga",
                "type": "auspicious",
                "category": "Dhana",
                "planets": [lord_2, lord_11],
                "description": (
                    f"{lord_2} (2nd lord) conjunct {lord_11} (11th lord) "
                    f"in house {h2l}. Income meets savings — wealth accumulation."
                ),
            })

    return yogas


def _viparita_raja(planets: list[dict], houses: list[dict]) -> list[dict]:
    """Viparita Raja Yoga: lords of 6, 8, 12 placed in other dusthanas."""
    lord_6 = _house_lord(houses, 6)
    lord_8 = _house_lord(houses, 8)
    lord_12 = _house_lord(houses, 12)
    dusthana_lords = {6: lord_6, 8: lord_8, 12: lord_12}
    yogas = []
    for h_num, lord in dusthana_lords.items():
        if not lord:
            continue
        placed_house = _planet_house(planets, lord)
        other_dusthanas = DUSTHANA_HOUSES - {h_num}
        if placed_house in other_dusthanas:
            yogas.append({
                "name": "Viparita Raja Yoga",
                "type": "auspicious",
                "category": "Special",
                "planets": [lord],
                "description": (
                    f"{lord} (lord of {h_num}) placed in dusthana {placed_house}. "
                    f"Obstacles of enemies become your advantage. "
                    f"Success through overcoming adversity."
                ),
            })
    return yogas


def _neecha_bhanga(planets: list[dict], houses: list[dict]) -> list[dict]:
    """Neecha Bhanga Raja Yoga: cancellation of debilitation."""
    exalts_in_sign: dict[str, str] = {}
    for planet_name, ex_sign in EXALTATION.items():
        exalts_in_sign[ex_sign] = planet_name

    yogas = []
    moon_house = _planet_house(planets, "Moon")

    for p in planets:
        if p["name"] in ("Rahu", "Ketu"):
            continue
        if p["sign"] != DEBILITATION.get(p["name"]):
            continue

        cancelled = False
        reasons: list[str] = []
        deb_sign = p["sign"]

        sign_lord = None
        for planet_name, signs in OWNERSHIP.items():
            if deb_sign in signs:
                sign_lord = planet_name
                break

        if sign_lord:
            sl_house = _planet_house(planets, sign_lord)
            if sl_house in KENDRA_HOUSES:
                cancelled = True
                reasons.append(f"{sign_lord} (lord of {deb_sign}) in kendra house {sl_house}")
            elif moon_house:
                kendras_from_moon = {_houses_from(moon_house, o) for o in (0, 3, 6, 9)}
                if sl_house in kendras_from_moon:
                    cancelled = True
                    reasons.append(f"{sign_lord} (lord of {deb_sign}) in kendra from Moon")

        exalt_planet = exalts_in_sign.get(deb_sign)
        if exalt_planet and exalt_planet != p["name"]:
            ep_house = _planet_house(planets, exalt_planet)
            if ep_house in KENDRA_HOUSES:
                cancelled = True
                reasons.append(f"{exalt_planet} (exalts in {deb_sign}) in kendra house {ep_house}")

        if p["house"] in KENDRA_HOUSES:
            cancelled = True
            reasons.append(f"{p['name']} debilitated but in kendra house {p['house']}")

        if sign_lord and sign_lord != p["name"]:
            if _is_aspected_by(p["house"], sign_lord, planets):
                cancelled = True
                reasons.append(f"{p['name']} aspected by {sign_lord} (lord of {deb_sign})")

        ex_sign = EXALTATION.get(p["name"])
        if ex_sign:
            ex_sign_lord = None
            for planet_name, signs in OWNERSHIP.items():
                if ex_sign in signs:
                    ex_sign_lord = planet_name
                    break
            if ex_sign_lord:
                esl_house = _planet_house(planets, ex_sign_lord)
                if esl_house in KENDRA_HOUSES:
                    cancelled = True
                    reasons.append(
                        f"{ex_sign_lord} (lord of {p['name']}'s exaltation sign {ex_sign}) "
                        f"in kendra house {esl_house}"
                    )

        if cancelled:
            yogas.append({
                "name": "Neecha Bhanga Raja Yoga",
                "type": "auspicious",
                "category": "Special",
                "planets": [p["name"]],
                "description": (
                    f"{p['name']} debilitated in {deb_sign} (house {p['house']}), "
                    f"but cancellation via: {'; '.join(reasons)}. "
                    f"Initial weakness transforms into extraordinary strength."
                ),
            })
    return yogas


def _parivartana(planets: list[dict], houses: list[dict]) -> list[dict]:
    """Parivartana Yoga (mutual exchange): two house lords in each other's houses."""
    yogas = []
    good_houses = {1, 2, 4, 5, 7, 9, 10, 11}
    dusthana = {6, 8, 12}
    seen: set[tuple[int, ...]] = set()

    for h_a in range(1, 13):
        lord_a = _house_lord(houses, h_a)
        if not lord_a:
            continue
        placed_a = _planet_house(planets, lord_a)
        if placed_a == 0 or placed_a == h_a:
            continue

        lord_b = _house_lord(houses, placed_a)
        if not lord_b or lord_b == lord_a:
            continue
        placed_b = _planet_house(planets, lord_b)
        if placed_b != h_a:
            continue

        pair = tuple(sorted([h_a, placed_a]))
        if pair in seen:
            continue
        seen.add(pair)

        a_good = h_a in good_houses
        b_good = placed_a in good_houses
        a_dusthana = h_a in dusthana
        b_dusthana = placed_a in dusthana

        if a_good and b_good:
            yoga_type = "auspicious"
            category = "Raja"
            if pair == (9, 10):
                name = "Dharma Karma Adhipati Yoga (Parivartana)"
                desc = (
                    f"{lord_a} (lord of {h_a}) and {lord_b} (lord of {placed_a}) "
                    f"in mutual exchange. Dharma and Karma unite — "
                    f"career success aligned with life purpose."
                )
            else:
                name = "Parivartana Yoga (Maha)"
                desc = (
                    f"{lord_a} (lord of {h_a}) and {lord_b} (lord of {placed_a}) "
                    f"in mutual exchange. Both houses strengthened."
                )
        elif a_dusthana and b_dusthana:
            yoga_type = "challenging"
            category = "Special"
            name = "Parivartana Yoga (Khala)"
            desc = (
                f"{lord_a} (lord of {h_a}) and {lord_b} (lord of {placed_a}) "
                f"in mutual exchange between dusthanas. Turbulent energy."
            )
        else:
            yoga_type = "challenging"
            category = "Special"
            name = "Parivartana Yoga (Dainya)"
            desc = (
                f"{lord_a} (lord of {h_a}) and {lord_b} (lord of {placed_a}) "
                f"in mutual exchange. Challenges leading to growth."
            )

        yogas.append({
            "name": name,
            "type": yoga_type,
            "category": category,
            "planets": sorted([lord_a, lord_b]),
            "description": desc,
        })

    return yogas


def _saraswati(planets: list[dict]) -> list[dict]:
    """Saraswati Yoga: Jupiter, Venus, Mercury all in kendras, trikonas, or 2nd."""
    good_houses = KENDRA_HOUSES | TRIKONA_HOUSES | {2}
    jup_h = _planet_house(planets, "Jupiter")
    ven_h = _planet_house(planets, "Venus")
    mer_h = _planet_house(planets, "Mercury")

    if jup_h in good_houses and ven_h in good_houses and mer_h in good_houses:
        return [{
            "name": "Saraswati Yoga",
            "type": "auspicious",
            "category": "Benefic",
            "planets": ["Jupiter", "Venus", "Mercury"],
            "description": (
                f"Jupiter (H{jup_h}), Venus (H{ven_h}), Mercury (H{mer_h}) — "
                f"all in good houses. Knowledge, arts, education, eloquence."
            ),
        }]
    return []


def _kemadruma(planets: list[dict]) -> list[dict]:
    """Kemadruma Yoga: no planets in 2nd or 12th from Moon."""
    moon_h = _planet_house(planets, "Moon")
    if not moon_h:
        return []

    h_before = _houses_from(moon_h, -1)
    h_after = _houses_from(moon_h, 1)

    flanking_candidates = [
        p for p in planets
        if p["name"] not in ("Sun", "Rahu", "Ketu", "Moon")
    ]
    flanking = [p for p in flanking_candidates if p["house"] in (h_before, h_after)]
    if flanking:
        return []

    # Cancellations
    if moon_h in KENDRA_HOUSES:
        return []
    conjunct_benefics = [
        p["name"] for p in flanking_candidates
        if p["house"] == moon_h and p["name"] in BENEFICS
    ]
    if conjunct_benefics:
        return []
    jup_h = _planet_house(planets, "Jupiter")
    if jup_h:
        jup_aspects = {
            _houses_from(jup_h, 6),
            _houses_from(jup_h, 4),
            _houses_from(jup_h, 8),
        }
        if moon_h in jup_aspects:
            return []

    return [{
        "name": "Kemadruma Yoga",
        "type": "challenging",
        "category": "Challenging",
        "planets": ["Moon"],
        "description": (
            f"No planets adjacent to Moon (houses {h_before} and {h_after} empty). "
            f"Emotional isolation, zero conversational padding."
        ),
    }]


def _sunapha_anapha_durudhara(planets: list[dict]) -> list[dict]:
    """Sunapha/Anapha/Durudhara Yogas based on planets in 2nd/12th from Moon."""
    moon_h = _planet_house(planets, "Moon")
    if not moon_h:
        return []

    h_2nd = _houses_from(moon_h, 1)
    h_12th = _houses_from(moon_h, -1)
    valid_names = {"Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
    in_2nd = [p["name"] for p in planets if p["house"] == h_2nd and p["name"] in valid_names]
    in_12th = [p["name"] for p in planets if p["house"] == h_12th and p["name"] in valid_names]

    yogas = []
    if in_2nd and in_12th:
        yogas.append({
            "name": "Durudhara Yoga",
            "type": "auspicious",
            "category": "Benefic",
            "planets": in_2nd + in_12th,
            "description": (
                f"Planets in both 2nd ({', '.join(in_2nd)}) and 12th ({', '.join(in_12th)}) "
                f"from Moon. Wealth, virtue, generous nature."
            ),
        })
    elif in_2nd:
        yogas.append({
            "name": "Sunapha Yoga",
            "type": "auspicious",
            "category": "Benefic",
            "planets": in_2nd,
            "description": f"{', '.join(in_2nd)} in 2nd from Moon. Self-made wealth, intelligence.",
        })
    elif in_12th:
        yogas.append({
            "name": "Anapha Yoga",
            "type": "auspicious",
            "category": "Benefic",
            "planets": in_12th,
            "description": f"{', '.join(in_12th)} in 12th from Moon. Strong physique, virtuous conduct.",
        })
    return yogas


def _adhi_yoga(planets: list[dict]) -> list[dict]:
    """Adhi Yoga: benefics in 6th, 7th, 8th from Moon."""
    moon_h = _planet_house(planets, "Moon")
    if not moon_h:
        return []

    target_houses = {
        _houses_from(moon_h, 5),
        _houses_from(moon_h, 6),
        _houses_from(moon_h, 7),
    }
    benefic_names = {"Jupiter", "Venus", "Mercury"}
    benefics_placed = [
        p["name"] for p in planets
        if p["name"] in benefic_names and p["house"] in target_houses
    ]
    if len(benefics_placed) >= 2:
        return [{
            "name": "Adhi Yoga",
            "type": "auspicious",
            "category": "Raja",
            "planets": benefics_placed,
            "description": (
                f"{', '.join(benefics_placed)} in 6th/7th/8th from Moon. "
                f"Leadership ability, political success."
            ),
        }]
    return []


def _shakata(planets: list[dict]) -> list[dict]:
    """Shakata Yoga: Jupiter in 6th, 8th, or 12th from Moon."""
    moon_h = _planet_house(planets, "Moon")
    jup_h = _planet_house(planets, "Jupiter")
    if not moon_h or not jup_h:
        return []

    bad_houses = {
        _houses_from(moon_h, 5),
        _houses_from(moon_h, 7),
        _houses_from(moon_h, 11),
    }
    if jup_h not in bad_houses:
        return []
    if jup_h in KENDRA_HOUSES:
        return []

    return [{
        "name": "Shakata Yoga",
        "type": "challenging",
        "category": "Challenging",
        "planets": ["Jupiter", "Moon"],
        "description": (
            f"Jupiter in difficult position from Moon (house {jup_h}). "
            f"Fluctuating fortune — periods of gain followed by loss."
        ),
    }]


_KALA_SARPA_VARIANTS: dict[int, str] = {
    1: "Ananta", 2: "Kulika", 3: "Vasuki", 4: "Shankhapala",
    5: "Padma", 6: "Mahapadma", 7: "Takshaka", 8: "Karkotaka",
    9: "Shankhachuda", 10: "Ghataka", 11: "Vishadhara", 12: "Sheshanaga",
}


def _kala_sarpa(planets: list[dict]) -> list[dict]:
    """Kala Sarpa Dosha: all 7 planets hemmed between Rahu and Ketu."""
    rahu_h = _planet_house(planets, "Rahu")
    ketu_h = _planet_house(planets, "Ketu")
    if not rahu_h or not ketu_h:
        return []

    visible = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    planet_houses = []
    for name in visible:
        h = _planet_house(planets, name)
        if h:
            planet_houses.append(h)
    if len(planet_houses) < 7:
        return []

    def _between_clockwise(start: int, end: int, house: int) -> bool:
        if start <= end:
            return start <= house <= end
        return house >= start or house <= end

    all_on_rahu_side = all(_between_clockwise(rahu_h, ketu_h, h) for h in planet_houses)
    all_on_ketu_side = all(_between_clockwise(ketu_h, rahu_h, h) for h in planet_houses)

    if not all_on_rahu_side and not all_on_ketu_side:
        return []

    variant = _KALA_SARPA_VARIANTS.get(rahu_h, "")
    variant_str = f" ({variant} Kala Sarpa)" if variant else ""

    return [{
        "name": f"Kala Sarpa Dosha{variant_str}",
        "type": "challenging",
        "category": "Challenging",
        "planets": ["Rahu", "Ketu"],
        "description": (
            f"All 7 planets hemmed between Rahu (H{rahu_h}) and Ketu (H{ketu_h}). "
            f"Karmic axis dominates — intense transformation, extreme outcomes."
        ),
    }]


def _mahabhagya(planets: list[dict], houses: list[dict]) -> list[dict]:
    """Mahabhagya Yoga — Great Fortune."""
    sun_sign = _planet_sign(planets, "Sun")
    moon_sign = _planet_sign(planets, "Moon")
    sun_house = _planet_house(planets, "Sun")
    if not sun_sign or not moon_sign or not sun_house:
        return []

    lagna_sign = ""
    for h in houses:
        if h["number"] == 1:
            lagna_sign = h["sign"]
            break
    if not lagna_sign:
        return []

    def _is_odd_sign(sign: str) -> bool:
        idx = SIGNS.index(sign) if sign in SIGNS else -1
        return idx % 2 == 0

    is_day = sun_house >= 7
    all_odd = all(_is_odd_sign(s) for s in [sun_sign, moon_sign, lagna_sign])
    all_even = all(not _is_odd_sign(s) for s in [sun_sign, moon_sign, lagna_sign])

    if is_day and all_odd:
        return [{
            "name": "Mahabhagya Yoga",
            "type": "auspicious",
            "category": "Raja",
            "planets": ["Sun", "Moon"],
            "description": "Day birth with Sun, Moon, Lagna in odd signs. Great fortune.",
        }]
    if not is_day and all_even:
        return [{
            "name": "Mahabhagya Yoga",
            "type": "auspicious",
            "category": "Raja",
            "planets": ["Sun", "Moon"],
            "description": "Night birth with Sun, Moon, Lagna in even signs. Great fortune.",
        }]
    return []


# --- Doshas ---

MANGLIK_HOUSES = {1, 2, 4, 7, 8, 12}

_MANGLIK_HOUSE_SIGN_CANCEL = {
    1: {"Aries", "Leo"}, 2: {"Gemini", "Virgo"},
    4: {"Aries", "Scorpio"}, 7: {"Cancer", "Capricorn"},
    8: {"Sagittarius", "Pisces"}, 12: {"Taurus", "Libra"},
}


def compute_manglik_status(planets: list[dict], houses: list[dict]) -> dict:
    """Canonical Manglik (Kuja) Dosha detection."""
    mars_h = _planet_house(planets, "Mars")
    if not mars_h:
        return {"is_manglik": False, "severity": "none", "cancelled": False,
                "reasons": [], "cancellation_reasons": []}

    mars_sign = _planet_sign(planets, "Mars")
    manglik_lagna = mars_h in MANGLIK_HOUSES

    moon_h = _planet_house(planets, "Moon")
    manglik_moon = False
    mars_from_moon = 0
    if moon_h:
        mars_from_moon = ((mars_h - moon_h) % 12) + 1
        manglik_moon = mars_from_moon in MANGLIK_HOUSES

    is_manglik = manglik_lagna or manglik_moon
    if not is_manglik:
        return {"is_manglik": False, "severity": "none", "cancelled": False,
                "reasons": [], "cancellation_reasons": []}

    reasons = []
    if manglik_lagna:
        reasons.append(f"Mars in {mars_h}th from Lagna")
    if manglik_moon:
        reasons.append(f"Mars in {mars_from_moon}th from Moon")

    severe_houses = {7, 8}
    if mars_h in severe_houses or (manglik_moon and mars_from_moon in severe_houses):
        severity = "severe"
    else:
        severity = "mild"
    if manglik_lagna and manglik_moon:
        severity = "severe" if severity == "severe" else "moderate"

    cancellation_reasons = []
    if mars_sign in OWNERSHIP.get("Mars", []):
        cancellation_reasons.append(f"Mars in own sign ({mars_sign})")
    if mars_sign == EXALTATION.get("Mars"):
        cancellation_reasons.append(f"Mars exalted in {mars_sign}")

    jup_h = _planet_house(planets, "Jupiter")
    if jup_h and jup_h == mars_h:
        cancellation_reasons.append("Mars conjunct Jupiter")
    elif _is_aspected_by(mars_h, "Jupiter", planets):
        cancellation_reasons.append("Mars aspected by Jupiter")

    sat_h = _planet_house(planets, "Saturn")
    if sat_h and sat_h == mars_h:
        cancellation_reasons.append("Mars conjunct Saturn")
    elif _is_aspected_by(mars_h, "Saturn", planets):
        cancellation_reasons.append("Mars aspected by Saturn")

    if mars_sign in ("Leo", "Aquarius"):
        cancellation_reasons.append(f"Mars in {mars_sign}")

    if manglik_lagna:
        cancel_signs = _MANGLIK_HOUSE_SIGN_CANCEL.get(mars_h, set())
        if mars_sign in cancel_signs:
            cancellation_reasons.append(f"Mars in {mars_h}th house in {mars_sign}")

    cancelled = len(cancellation_reasons) > 0
    return {
        "is_manglik": True,
        "severity": "cancelled" if cancelled else severity,
        "cancelled": cancelled,
        "reasons": reasons,
        "cancellation_reasons": cancellation_reasons,
    }


def _manglik_dosha(planets: list[dict], houses: list[dict]) -> list[dict]:
    """Manglik (Kuja) Dosha."""
    status = compute_manglik_status(planets, houses)
    if not status["is_manglik"]:
        return []

    mars_h = _planet_house(planets, "Mars")
    mars_sign = _planet_sign(planets, "Mars")

    if status["cancelled"]:
        return [{
            "name": "Manglik Dosha (cancelled)",
            "type": "challenging",
            "category": "Dosha",
            "planets": ["Mars"],
            "description": (
                f"Mars in house {mars_h} ({mars_sign}) — Manglik position. "
                f"Cancelled: {'; '.join(status['cancellation_reasons'])}."
            ),
        }]

    return [{
        "name": "Manglik Dosha",
        "type": "challenging",
        "category": "Dosha",
        "planets": ["Mars"],
        "description": (
            f"Mars in house {mars_h} ({mars_sign}) — Manglik ({status['severity']}). "
            f"May cause friction in partnerships."
        ),
    }]


def _guru_chandal_dosha(planets: list[dict]) -> list[dict]:
    """Guru Chandal Dosha: Jupiter conjunct Rahu or Ketu."""
    jup_h = _planet_house(planets, "Jupiter")
    if not jup_h:
        return []

    rahu_h = _planet_house(planets, "Rahu")
    ketu_h = _planet_house(planets, "Ketu")

    node = None
    if rahu_h == jup_h:
        node = "Rahu"
    elif ketu_h == jup_h:
        node = "Ketu"
    if not node:
        return []

    return [{
        "name": "Guru Chandal Dosha",
        "type": "challenging",
        "category": "Dosha",
        "planets": ["Jupiter", node],
        "description": (
            f"Jupiter conjunct {node} in house {jup_h}. "
            f"Wisdom clouded — unconventional beliefs, hallucination-prone."
        ),
    }]


def _shrapit_dosha(planets: list[dict]) -> list[dict]:
    """Shrapit Dosha: Saturn conjunct Rahu."""
    sat_h = _planet_house(planets, "Saturn")
    rahu_h = _planet_house(planets, "Rahu")
    if not sat_h or sat_h != rahu_h:
        return []
    return [{
        "name": "Shrapit Dosha",
        "type": "challenging",
        "category": "Dosha",
        "planets": ["Saturn", "Rahu"],
        "description": f"Saturn conjunct Rahu in house {sat_h}. Karmic debt — delays and obstacles.",
    }]


def _grahan_dosha(planets: list[dict]) -> list[dict]:
    """Grahan (Eclipse) Dosha: Sun or Moon conjunct Rahu or Ketu."""
    yogas = []
    rahu_h = _planet_house(planets, "Rahu")
    ketu_h = _planet_house(planets, "Ketu")

    for luminary in ("Sun", "Moon"):
        lum_h = _planet_house(planets, luminary)
        if not lum_h:
            continue
        node = None
        if lum_h == rahu_h:
            node = "Rahu"
        elif lum_h == ketu_h:
            node = "Ketu"
        if not node:
            continue

        lum_lon = _planet_longitude(planets, luminary)
        node_lon = _planet_longitude(planets, node)
        tight = False
        if lum_lon is not None and node_lon is not None:
            diff = abs(lum_lon - node_lon)
            if diff > 180:
                diff = 360 - diff
            tight = diff < 15

        severity = "tight orb" if tight else "wide conjunction"
        yogas.append({
            "name": f"Grahan Dosha ({luminary})",
            "type": "challenging",
            "category": "Dosha",
            "planets": [luminary, node],
            "description": f"{luminary} conjunct {node} in house {lum_h} — {severity}.",
        })
    return yogas


def _pitri_dosha(planets: list[dict], houses: list[dict]) -> list[dict]:
    """Pitri Dosha: affliction to Sun/9th house."""
    sun_h = _planet_house(planets, "Sun")
    rahu_h = _planet_house(planets, "Rahu")
    ketu_h = _planet_house(planets, "Ketu")
    lord_9 = _house_lord(houses, 9)

    reasons = []
    if sun_h and (sun_h == rahu_h or sun_h == ketu_h):
        node = "Rahu" if sun_h == rahu_h else "Ketu"
        reasons.append(f"Sun conjunct {node} in house {sun_h}")
    if sun_h == 9:
        if _is_aspected_by(9, "Saturn", planets):
            reasons.append("Sun in 9th aspected by Saturn")
        if _is_aspected_by(9, "Rahu", planets):
            reasons.append("Sun in 9th aspected by Rahu")
    if lord_9 and rahu_h:
        lord_9_h = _planet_house(planets, lord_9)
        if lord_9_h == rahu_h:
            reasons.append(f"9th lord ({lord_9}) conjunct Rahu in house {rahu_h}")

    if not reasons:
        return []
    return [{
        "name": "Pitri Dosha",
        "type": "challenging",
        "category": "Dosha",
        "planets": ["Sun"],
        "description": f"Ancestral karma: {'; '.join(reasons)}.",
    }]


def _angarak_dosha(planets: list[dict]) -> list[dict]:
    """Angarak Dosha: Mars conjunct Rahu or Ketu."""
    mars_h = _planet_house(planets, "Mars")
    if not mars_h:
        return []
    rahu_h = _planet_house(planets, "Rahu")
    ketu_h = _planet_house(planets, "Ketu")
    node = None
    if mars_h == rahu_h:
        node = "Rahu"
    elif mars_h == ketu_h:
        node = "Ketu"
    if not node:
        return []
    return [{
        "name": "Angarak Dosha",
        "type": "challenging",
        "category": "Dosha",
        "planets": ["Mars", node],
        "description": f"Mars conjunct {node} in house {mars_h}. Explosive energy, impulsive actions.",
    }]


def _vish_dosha(planets: list[dict]) -> list[dict]:
    """Vish (Poison) Dosha: Moon conjunct Saturn."""
    moon_h = _planet_house(planets, "Moon")
    sat_h = _planet_house(planets, "Saturn")
    if not moon_h or moon_h != sat_h:
        return []

    jup_aspect = _is_aspected_by(moon_h, "Jupiter", planets)
    name = "Vish Dosha (mitigated)" if jup_aspect else "Vish Dosha"
    desc = (
        f"Moon conjunct Saturn in house {moon_h}. "
        + ("Jupiter's aspect provides relief." if jup_aspect else "Emotional heaviness, pessimism.")
    )
    return [{
        "name": name,
        "type": "challenging",
        "category": "Dosha",
        "planets": ["Moon", "Saturn"],
        "description": desc,
    }]


# --- Solar Yogas ---

def _vesi_vasi_ubhayachari(planets: list[dict]) -> list[dict]:
    """Vesi/Vasi/Ubhayachari Yogas: planets flanking the Sun."""
    sun_h = _planet_house(planets, "Sun")
    if not sun_h:
        return []

    h_2nd = _houses_from(sun_h, 1)
    h_12th = _houses_from(sun_h, -1)
    excluded = {"Sun", "Moon", "Rahu", "Ketu"}
    in_2nd = [p["name"] for p in planets if p["house"] == h_2nd and p["name"] not in excluded]
    in_12th = [p["name"] for p in planets if p["house"] == h_12th and p["name"] not in excluded]

    yogas = []
    if in_2nd and in_12th:
        yogas.append({
            "name": "Ubhayachari Yoga",
            "type": "auspicious",
            "category": "Benefic",
            "planets": in_2nd + in_12th,
            "description": "Planets flanking Sun from both sides. Royal bearing, fame, leadership.",
        })
    elif in_2nd:
        yogas.append({
            "name": "Vesi Yoga",
            "type": "auspicious",
            "category": "Benefic",
            "planets": in_2nd,
            "description": f"{', '.join(in_2nd)} in 2nd from Sun. Wealth, eloquent speech.",
        })
    elif in_12th:
        yogas.append({
            "name": "Vasi Yoga",
            "type": "auspicious",
            "category": "Benefic",
            "planets": in_12th,
            "description": f"{', '.join(in_12th)} in 12th from Sun. Charitable, spiritual.",
        })
    return yogas


# --- Kartari Yogas ---

def _kartari_yogas(planets: list[dict]) -> list[dict]:
    """Papa/Shubha Kartari: house hemmed between malefics/benefics."""
    yogas = []
    strict_benefics = {"Jupiter", "Venus"}
    strict_malefics = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}

    moon_h = _planet_house(planets, "Moon")
    targets = [(1, "Lagna")]
    if moon_h and moon_h != 1:
        targets.append((moon_h, "Moon"))

    for house, label in targets:
        h_prev = _houses_from(house, -1)
        h_next = _houses_from(house, 1)
        planets_prev = {p["name"] for p in planets if p["house"] == h_prev}
        planets_next = {p["name"] for p in planets if p["house"] == h_next}

        if (planets_prev & strict_malefics) and (planets_next & strict_malefics):
            yogas.append({
                "name": f"Papa Kartari ({label})",
                "type": "challenging",
                "category": "Challenging",
                "planets": sorted((planets_prev | planets_next) & strict_malefics),
                "description": f"{label} hemmed between malefics. Restriction and pressure.",
            })
        elif (planets_prev & strict_benefics) and (planets_next & strict_benefics):
            yogas.append({
                "name": f"Shubha Kartari ({label})",
                "type": "auspicious",
                "category": "Benefic",
                "planets": sorted((planets_prev | planets_next) & strict_benefics),
                "description": f"{label} hemmed between benefics. Protection and support.",
            })
    return yogas


# --- Nabhasa Sankhya ---

_SANKHYA_NAMES: dict[int, tuple[str, str]] = {
    1: ("Gola Yoga", "All planets in 1 sign — extremely focused"),
    2: ("Yuga Yoga", "Planets in 2 signs — dual focus"),
    3: ("Shula Yoga", "Planets in 3 signs — triangular focus"),
    4: ("Kedara Yoga", "Planets in 4 signs — balanced, practical"),
    5: ("Pasha Yoga", "Planets in 5 signs — many responsibilities"),
    6: ("Dama Yoga", "Planets in 6 signs — generous spread, adaptable"),
    7: ("Veena Yoga", "Planets in 7 signs — widest spread, versatile"),
}


def _sankhya_nabhasa(planets: list[dict]) -> list[dict]:
    classical = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
    occupied_signs = {p["sign"] for p in planets if p["name"] in classical and p.get("sign")}
    count = len(occupied_signs)
    if count not in _SANKHYA_NAMES:
        return []
    name, desc = _SANKHYA_NAMES[count]
    yoga_type = "auspicious" if count >= 5 else ("challenging" if count <= 2 else "auspicious")
    return [{
        "name": name,
        "type": yoga_type,
        "category": "Nabhasa",
        "planets": [],
        "description": f"7 classical planets occupy {count} signs. {desc}.",
    }]


# --- Named Yogas ---

def _lakshmi_yoga(planets: list[dict], houses: list[dict]) -> list[dict]:
    lord_9 = _house_lord(houses, 9)
    lord_1 = _house_lord(houses, 1)
    if not lord_9 or not lord_1:
        return []
    lord_9_h = _planet_house(planets, lord_9)
    if lord_9_h not in KENDRA_HOUSES:
        return []
    lord_9_dig = _planet_dignity(planets, lord_9)
    if lord_9_dig not in ("exalted", "moolatrikona", "own_sign"):
        return []
    lord_1_dig = _planet_dignity(planets, lord_1)
    if lord_1_dig in ("debilitated", "enemy"):
        return []
    return [{
        "name": "Lakshmi Yoga",
        "type": "auspicious",
        "category": "Dhana",
        "planets": [lord_9, lord_1],
        "description": f"9th lord {lord_9} ({lord_9_dig}) in kendra H{lord_9_h}. Wealth and fortune.",
    }]


def _gauri_yoga(planets: list[dict]) -> list[dict]:
    moon_h = _planet_house(planets, "Moon")
    if not moon_h:
        return []
    moon_dig = _planet_dignity(planets, "Moon")
    if moon_dig not in ("exalted", "own_sign", "moolatrikona"):
        return []
    if not _is_aspected_by(moon_h, "Jupiter", planets):
        jup_h = _planet_house(planets, "Jupiter")
        if jup_h != moon_h:
            return []
    return [{
        "name": "Gauri Yoga",
        "type": "auspicious",
        "category": "Benefic",
        "planets": ["Moon", "Jupiter"],
        "description": f"Moon ({moon_dig}) with Jupiter's blessing. Grace, emotional intelligence.",
    }]


def _kalanidhi_yoga(planets: list[dict]) -> list[dict]:
    jup_h = _planet_house(planets, "Jupiter")
    if jup_h not in (2, 5):
        return []
    mer_h = _planet_house(planets, "Mercury")
    ven_h = _planet_house(planets, "Venus")
    mer_connected = (mer_h == jup_h) or _is_aspected_by(jup_h, "Mercury", planets)
    ven_connected = (ven_h == jup_h) or _is_aspected_by(jup_h, "Venus", planets)
    if not (mer_connected and ven_connected):
        return []
    return [{
        "name": "Kalanidhi Yoga",
        "type": "auspicious",
        "category": "Benefic",
        "planets": ["Jupiter", "Mercury", "Venus"],
        "description": f"Jupiter in H{jup_h} with Mercury and Venus. Mastery of arts and sciences.",
    }]


def _chamara_yoga(planets: list[dict], houses: list[dict]) -> list[dict]:
    lord_1 = _house_lord(houses, 1)
    if not lord_1:
        return []
    lord_1_h = _planet_house(planets, lord_1)
    lord_1_dig = _planet_dignity(planets, lord_1)
    if lord_1_h not in KENDRA_HOUSES or lord_1_dig != "exalted":
        return []
    jup_h = _planet_house(planets, "Jupiter")
    if (jup_h != lord_1_h) and not _is_aspected_by(lord_1_h, "Jupiter", planets):
        return []
    return [{
        "name": "Chamara Yoga",
        "type": "auspicious",
        "category": "Raja",
        "planets": [lord_1, "Jupiter"],
        "description": f"Lagna lord {lord_1} exalted in kendra H{lord_1_h}, blessed by Jupiter.",
    }]


def _parvata_yoga(planets: list[dict], houses: list[dict]) -> list[dict]:
    benefics_in_kendras = [
        p["name"] for p in planets
        if p["name"] in BENEFICS and p["house"] in KENDRA_HOUSES
        and p["name"] not in ("Rahu", "Ketu")
    ]
    if len(benefics_in_kendras) < 2:
        return []
    strict_malefics = {"Mars", "Saturn", "Rahu", "Ketu"}
    malefics_in_68 = [
        p["name"] for p in planets
        if p["name"] in strict_malefics and p["house"] in (6, 8)
    ]
    if malefics_in_68:
        return []
    return [{
        "name": "Parvata Yoga",
        "type": "auspicious",
        "category": "Raja",
        "planets": benefics_in_kendras,
        "description": f"{', '.join(benefics_in_kendras)} in kendras, H6/H8 free. Firm reputation.",
    }]


def _kahala_yoga(planets: list[dict], houses: list[dict]) -> list[dict]:
    lord_4 = _house_lord(houses, 4)
    lord_9 = _house_lord(houses, 9)
    lord_1 = _house_lord(houses, 1)
    if not lord_4 or not lord_9 or not lord_1 or lord_4 == lord_9:
        return []
    h_4l = _planet_house(planets, lord_4)
    h_9l = _planet_house(planets, lord_9)
    if not h_4l or not h_9l:
        return []
    kendras_from_4l = {_houses_from(h_4l, o) for o in (0, 3, 6, 9)}
    if h_9l not in kendras_from_4l:
        return []
    lord_1_dig = _planet_dignity(planets, lord_1)
    if lord_1_dig == "debilitated":
        return []
    return [{
        "name": "Kahala Yoga",
        "type": "auspicious",
        "category": "Raja",
        "planets": [lord_4, lord_9],
        "description": f"4th lord ({lord_4}) and 9th lord ({lord_9}) in mutual kendras. Bold nature.",
    }]


def _akhanda_samrajya(planets: list[dict], houses: list[dict]) -> list[dict]:
    jup_h = _planet_house(planets, "Jupiter")
    if jup_h not in KENDRA_HOUSES:
        return []
    jup_houses_ruled = [h["number"] for h in houses if h["lord"] == "Jupiter"]
    target_houses = {2, 5, 11}
    if not (set(jup_houses_ruled) & target_houses):
        return []
    other_benefics = [
        p["name"] for p in planets
        if p["name"] in BENEFICS and p["house"] in KENDRA_HOUSES
        and p["name"] != "Jupiter" and p["name"] not in ("Rahu", "Ketu")
    ]
    if not other_benefics:
        return []
    return [{
        "name": "Akhanda Samrajya Yoga",
        "type": "auspicious",
        "category": "Raja",
        "planets": ["Jupiter"] + other_benefics,
        "description": f"Jupiter in kendra H{jup_h}, supported by {', '.join(other_benefics)}.",
    }]


# --- Two-planet combinations ---

def _guru_mangala(planets: list[dict]) -> list[dict]:
    jup_h = _planet_house(planets, "Jupiter")
    mars_h = _planet_house(planets, "Mars")
    if not jup_h or not mars_h:
        return []
    conjunct = jup_h == mars_h
    mutual_aspect = (
        _is_aspected_by(mars_h, "Jupiter", planets) and
        _is_aspected_by(jup_h, "Mars", planets)
    )
    if not conjunct and not mutual_aspect:
        return []
    return [{
        "name": "Guru-Mangala Yoga",
        "type": "auspicious",
        "category": "Benefic",
        "planets": ["Jupiter", "Mars"],
        "description": "Jupiter and Mars connected. Wisdom + courage, righteous action.",
    }]


def _shani_mangala(planets: list[dict]) -> list[dict]:
    sat_h = _planet_house(planets, "Saturn")
    mars_h = _planet_house(planets, "Mars")
    if not sat_h or not mars_h:
        return []
    conjunct = sat_h == mars_h
    mutual_aspect = (
        _is_aspected_by(mars_h, "Saturn", planets) and
        _is_aspected_by(sat_h, "Mars", planets)
    )
    if not conjunct and not mutual_aspect:
        return []
    return [{
        "name": "Shani-Mangala Yoga",
        "type": "challenging",
        "category": "Challenging",
        "planets": ["Saturn", "Mars"],
        "description": "Saturn and Mars connected. Fire meets ice — internal friction.",
    }]


def _pravrajya(planets: list[dict]) -> list[dict]:
    """Pravrajya (Sannyasa) Yoga: 4+ classical planets in one house."""
    classical = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
    house_planets: dict[int, list[str]] = {}
    for p in planets:
        if p["name"] in classical:
            house_planets.setdefault(p["house"], []).append(p["name"])
    yogas = []
    for house, pnames in house_planets.items():
        if len(pnames) >= 4:
            yogas.append({
                "name": "Pravrajya Yoga",
                "type": "auspicious",
                "category": "Special",
                "planets": sorted(pnames),
                "description": (
                    f"{len(pnames)} planets in house {house}. "
                    f"Deep philosophical nature, renunciation tendency."
                ),
            })
    return yogas


# --- Daridra Yogas ---

def _daridra_yogas(planets: list[dict], houses: list[dict]) -> list[dict]:
    yogas = []
    dusthanas = {6, 8, 12}

    lord_11 = _house_lord(houses, 11)
    if lord_11:
        h_11l = _planet_house(planets, lord_11)
        lord_11_dig = _planet_dignity(planets, lord_11)
        if h_11l in dusthanas and lord_11_dig in ("debilitated", "enemy", "neutral"):
            yogas.append({
                "name": "Daridra Yoga",
                "type": "challenging",
                "category": "Challenging",
                "planets": [lord_11],
                "description": f"11th lord ({lord_11}) in dusthana H{h_11l}. Income faces obstacles.",
            })

    lord_2 = _house_lord(houses, 2)
    if lord_2:
        h_2l = _planet_house(planets, lord_2)
        lord_2_dig = _planet_dignity(planets, lord_2)
        if h_2l in dusthanas and lord_2_dig in ("debilitated", "enemy"):
            yogas.append({
                "name": "Daridra Yoga",
                "type": "challenging",
                "category": "Challenging",
                "planets": [lord_2],
                "description": f"2nd lord ({lord_2}, {lord_2_dig}) in dusthana H{h_2l}.",
            })

    lord_5 = _house_lord(houses, 5)
    if lord_5:
        h_5l = _planet_house(planets, lord_5)
        lord_5_dig = _planet_dignity(planets, lord_5)
        if h_5l in dusthanas and lord_5_dig in ("debilitated", "enemy"):
            yogas.append({
                "name": "Daridra Yoga",
                "type": "challenging",
                "category": "Challenging",
                "planets": [lord_5],
                "description": f"5th lord ({lord_5}, {lord_5_dig}) in dusthana H{h_5l}.",
            })

    return yogas


# --- Batch 2: More Named Yogas ---

def _bheri_yoga(planets: list[dict], houses: list[dict]) -> list[dict]:
    lord_1 = _house_lord(houses, 1)
    lord_9 = _house_lord(houses, 9)
    if not lord_1 or not lord_9:
        return []
    ven_h = _planet_house(planets, "Venus")
    jup_h = _planet_house(planets, "Jupiter")
    l1_h = _planet_house(planets, lord_1)
    if not all(h in KENDRA_HOUSES for h in (ven_h, jup_h, l1_h) if h):
        return []
    lord_9_dig = _planet_dignity(planets, lord_9)
    if lord_9_dig in ("debilitated", "enemy"):
        return []
    return [{
        "name": "Bheri Yoga",
        "type": "auspicious",
        "category": "Dhana",
        "planets": ["Venus", "Jupiter", lord_1],
        "description": "Venus, Jupiter, and Lagna lord in kendras. Resonant prosperity.",
    }]


def _vasumathi_yoga(planets: list[dict]) -> list[dict]:
    benefic_names = {"Jupiter", "Venus", "Mercury"}
    strict_malefics = {"Mars", "Saturn", "Rahu", "Ketu"}
    bases = [1]
    moon_h = _planet_house(planets, "Moon")
    if moon_h and moon_h != 1:
        bases.append(moon_h)

    for base in bases:
        upachaya = {
            _houses_from(base, 2), _houses_from(base, 5),
            _houses_from(base, 9), _houses_from(base, 10),
        }
        benefics_in_upa = [
            p["name"] for p in planets if p["name"] in benefic_names and p["house"] in upachaya
        ]
        malefics_in_upa = [
            p["name"] for p in planets if p["name"] in strict_malefics and p["house"] in upachaya
        ]
        if len(benefics_in_upa) >= 2 and not malefics_in_upa:
            return [{
                "name": "Vasumathi Yoga",
                "type": "auspicious",
                "category": "Dhana",
                "planets": benefics_in_upa,
                "description": f"{', '.join(benefics_in_upa)} in upachaya houses. Steady wealth growth.",
            }]
    return []


def _srinatha_yoga(planets: list[dict], houses: list[dict]) -> list[dict]:
    lord_7 = _house_lord(houses, 7)
    lord_10 = _house_lord(houses, 10)
    if not lord_7 or not lord_10:
        return []
    h_7l = _planet_house(planets, lord_7)
    lord_10_dig = _planet_dignity(planets, lord_10)
    if h_7l == 10 and lord_10_dig == "exalted":
        return [{
            "name": "Srinatha Yoga",
            "type": "auspicious",
            "category": "Raja",
            "planets": [lord_7, lord_10],
            "description": "7th lord in 10th, 10th lord exalted. Partnership elevates career.",
        }]
    return []


def _vidyut_yoga(planets: list[dict], houses: list[dict]) -> list[dict]:
    lord_11 = _house_lord(houses, 11)
    if not lord_11:
        return []
    lord_11_dig = _planet_dignity(planets, lord_11)
    ven_h = _planet_house(planets, "Venus")
    if lord_11_dig == "exalted" and ven_h in KENDRA_HOUSES:
        return [{
            "name": "Vidyut Yoga",
            "type": "auspicious",
            "category": "Dhana",
            "planets": [lord_11, "Venus"],
            "description": f"11th lord ({lord_11}, exalted) + Venus in kendra. Lightning-like gains.",
        }]
    return []


def _pushti_yoga(planets: list[dict], houses: list[dict]) -> list[dict]:
    lord_1 = _house_lord(houses, 1)
    if not lord_1:
        return []
    lord_1_dig = _planet_dignity(planets, lord_1)
    lord_1_h = _planet_house(planets, lord_1)
    if lord_1_dig not in ("friend", "own_sign", "moolatrikona", "exalted"):
        return []
    jup_h = _planet_house(planets, "Jupiter")
    if (jup_h != lord_1_h) and not _is_aspected_by(lord_1_h, "Jupiter", planets):
        return []
    return [{
        "name": "Pushti Yoga",
        "type": "auspicious",
        "category": "Benefic",
        "planets": [lord_1, "Jupiter"],
        "description": f"Lagna lord {lord_1} ({lord_1_dig}) blessed by Jupiter. Growth and nourishment.",
    }]


def _parijata_yoga(planets: list[dict], houses: list[dict]) -> list[dict]:
    lord_1 = _house_lord(houses, 1)
    if not lord_1:
        return []
    lord_1_sign = _planet_sign(planets, lord_1)
    d1 = SIGN_LORDS.get(lord_1_sign)
    if not d1 or d1 == lord_1:
        d1 = lord_1
    d1_h = _planet_house(planets, d1)
    good_houses = KENDRA_HOUSES | TRIKONA_HOUSES
    if d1_h not in good_houses:
        return []
    d1_sign = _planet_sign(planets, d1)
    d2 = SIGN_LORDS.get(d1_sign)
    if not d2:
        return []
    if d2 == d1:
        return [{
            "name": "Parijata Yoga",
            "type": "auspicious",
            "category": "Raja",
            "planets": [lord_1, d1],
            "description": f"Strong dispositor chain — {d1} self-disposited in H{d1_h}.",
        }]
    d2_h = _planet_house(planets, d2)
    if d2_h not in good_houses:
        return []
    return [{
        "name": "Parijata Yoga",
        "type": "auspicious",
        "category": "Raja",
        "planets": [lord_1, d1, d2],
        "description": f"Dispositor chain: {lord_1} -> {d1} (H{d1_h}) -> {d2} (H{d2_h}).",
    }]


# --- Batch 4: Remaining ---

def _pushkala_yoga(planets: list[dict], houses: list[dict]) -> list[dict]:
    lord_1 = _house_lord(houses, 1)
    moon_sign = _planet_sign(planets, "Moon")
    moon_disp = SIGN_LORDS.get(moon_sign, "")
    if not lord_1 or not moon_disp:
        return []
    l1_h = _planet_house(planets, lord_1)
    disp_h = _planet_house(planets, moon_disp)
    if not l1_h or not disp_h:
        return []
    if lord_1 == moon_disp:
        conj_house = l1_h
    elif l1_h != disp_h:
        return []
    else:
        conj_house = l1_h
    disp_dig = _planet_dignity(planets, moon_disp)
    in_kendra = conj_house in KENDRA_HOUSES
    in_good_dignity = disp_dig in ("friend", "own_sign", "moolatrikona", "exalted")
    if not in_kendra and not in_good_dignity:
        return []
    benefic_aspects_lagna = False
    for ben in ("Jupiter", "Venus", "Mercury"):
        if _is_aspected_by(1, ben, planets) or _planet_house(planets, ben) == 1:
            ben_dig = _planet_dignity(planets, ben)
            if ben_dig != "debilitated":
                benefic_aspects_lagna = True
                break
    if not benefic_aspects_lagna:
        return []
    return [{
        "name": "Pushkala Yoga",
        "type": "auspicious",
        "category": "Dhana",
        "planets": sorted(set([lord_1, moon_disp])),
        "description": "Moon's dispositor + Lagna lord conjunct. Wealth, fame, royal honors.",
    }]


def _gandharva_yoga(planets: list[dict], houses: list[dict]) -> list[dict]:
    lord_10 = _house_lord(houses, 10)
    lord_1 = _house_lord(houses, 1)
    if not lord_10 or not lord_1:
        return []
    if _planet_house(planets, lord_10) not in (3, 7, 11):
        return []
    if _planet_house(planets, "Moon") != 9:
        return []
    l1_h = _planet_house(planets, lord_1)
    jup_h = _planet_house(planets, "Jupiter")
    if not l1_h or not jup_h:
        return []
    if lord_1 != "Jupiter" and l1_h != jup_h:
        return []
    sun_dig = _planet_dignity(planets, "Sun")
    if sun_dig not in ("exalted", "own_sign", "moolatrikona"):
        return []
    return [{
        "name": "Gandharva Yoga",
        "type": "auspicious",
        "category": "Benefic",
        "planets": [lord_10, lord_1, "Jupiter", "Moon", "Sun"],
        "description": "Celestial artistry — mastery in fine arts, music, cultural achievement.",
    }]


def _bhrigu_mangala(planets: list[dict]) -> list[dict]:
    ven_h = _planet_house(planets, "Venus")
    mars_h = _planet_house(planets, "Mars")
    if not ven_h or not mars_h:
        return []
    conjunct = ven_h == mars_h
    mutual_aspect = (
        _is_aspected_by(mars_h, "Venus", planets) and
        _is_aspected_by(ven_h, "Mars", planets)
    )
    if not conjunct and not mutual_aspect:
        return []
    return [{
        "name": "Bhrigu-Mangala Yoga",
        "type": "auspicious",
        "category": "Dhana",
        "planets": ["Venus", "Mars"],
        "description": "Venus + Mars connected. Passion meets prosperity.",
    }]


def _vargottama_yoga(planets: list[dict], houses: list[dict]) -> list[dict]:
    """Vargottama: planets in same sign in D1 and D9."""
    movable = {"Aries", "Cancer", "Libra", "Capricorn"}
    fixed = {"Taurus", "Leo", "Scorpio", "Aquarius"}
    dual = {"Gemini", "Virgo", "Sagittarius", "Pisces"}

    vargottama_planets = []
    for p in planets:
        sign = p.get("sign", "")
        lon = p.get("longitude")
        if not sign or lon is None:
            continue
        deg_in_sign = lon % 30
        t_3_20 = 3 + 20 / 60
        t_13_20 = 13 + 20 / 60
        t_16_40 = 16 + 40 / 60
        t_26_40 = 26 + 40 / 60

        is_vargottama = False
        if sign in movable and 0 <= deg_in_sign < t_3_20:
            is_vargottama = True
        elif sign in fixed and t_13_20 <= deg_in_sign < t_16_40:
            is_vargottama = True
        elif sign in dual and t_26_40 <= deg_in_sign <= 30:
            is_vargottama = True

        if is_vargottama:
            vargottama_planets.append(p["name"])

    if not vargottama_planets:
        return []
    return [{
        "name": "Vargottama Yoga",
        "type": "auspicious",
        "category": "Special",
        "planets": vargottama_planets,
        "description": (
            f"{', '.join(vargottama_planets)} in same sign in D1 and D9. "
            f"Integrated expression — consistent, reliable results."
        ),
    }]


# --- Batch 3: Two-planet combinations ---

def _chandra_guru(planets: list[dict]) -> list[dict]:
    moon_h = _planet_house(planets, "Moon")
    jup_h = _planet_house(planets, "Jupiter")
    if not moon_h or moon_h != jup_h:
        return []
    if _planet_sign(planets, "Moon") != _planet_sign(planets, "Jupiter"):
        return []
    return [{
        "name": "Chandra-Guru Yoga",
        "type": "auspicious",
        "category": "Benefic",
        "planets": ["Moon", "Jupiter"],
        "description": f"Moon and Jupiter conjunct in H{moon_h}. Emotional wisdom, intuitive intelligence.",
    }]


def _chandra_shukra(planets: list[dict]) -> list[dict]:
    moon_h = _planet_house(planets, "Moon")
    ven_h = _planet_house(planets, "Venus")
    if not moon_h or moon_h != ven_h:
        return []
    return [{
        "name": "Chandra-Shukra Yoga",
        "type": "auspicious",
        "category": "Benefic",
        "planets": ["Moon", "Venus"],
        "description": f"Moon and Venus conjunct in H{moon_h}. Charm, beauty, artistic grace.",
    }]


def _shukra_aditya(planets: list[dict]) -> list[dict]:
    sun_h = _planet_house(planets, "Sun")
    ven_h = _planet_house(planets, "Venus")
    if not sun_h or sun_h != ven_h:
        return []

    sun_lon = _planet_longitude(planets, "Sun")
    ven_lon = _planet_longitude(planets, "Venus")
    combust = False
    if sun_lon is not None and ven_lon is not None:
        diff = abs(sun_lon - ven_lon)
        if diff > 180:
            diff = 360 - diff
        ven_retro = any(p["name"] == "Venus" and p.get("motion") == "retrograde" for p in planets)
        orb = COMBUSTION_ORBS_RETROGRADE.get("Venus", 10.0) if ven_retro else COMBUSTION_ORBS.get("Venus", 10.0)
        combust = diff <= orb

    if combust:
        return [{
            "name": "Shukra-Aditya Yoga (combust)",
            "type": "challenging",
            "category": "Challenging",
            "planets": ["Sun", "Venus"],
            "description": f"Sun and Venus in H{sun_h}, Venus combust. Expression suppressed.",
        }]
    return [{
        "name": "Shukra-Aditya Yoga",
        "type": "auspicious",
        "category": "Benefic",
        "planets": ["Sun", "Venus"],
        "description": f"Sun and Venus in H{sun_h}. Authority + charm, success in arts.",
    }]


def _guru_shani(planets: list[dict]) -> list[dict]:
    jup_h = _planet_house(planets, "Jupiter")
    sat_h = _planet_house(planets, "Saturn")
    if not jup_h or not sat_h:
        return []
    conjunct = jup_h == sat_h
    mutual_aspect = (
        _is_aspected_by(sat_h, "Jupiter", planets) and
        _is_aspected_by(jup_h, "Saturn", planets)
    )
    if not conjunct and not mutual_aspect:
        return []
    return [{
        "name": "Guru-Shani Yoga",
        "type": "auspicious",
        "category": "Special",
        "planets": ["Jupiter", "Saturn"],
        "description": "Jupiter + Saturn connected. Structured growth, delayed but enduring results.",
    }]


# --- Nabhasa Ashraya + Dala ---

def _nabhasa_ashraya(planets: list[dict]) -> list[dict]:
    classical = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
    movable = {"Aries", "Cancer", "Libra", "Capricorn"}
    fixed = {"Taurus", "Leo", "Scorpio", "Aquarius"}
    dual = {"Gemini", "Virgo", "Sagittarius", "Pisces"}
    signs = [p["sign"] for p in planets if p["name"] in classical and p.get("sign")]
    if len(signs) < 7:
        return []
    if all(s in movable for s in signs):
        return [{"name": "Rajju Yoga (Nabhasa)", "type": "auspicious", "category": "Nabhasa",
                 "planets": [], "description": "All planets in movable signs. Dynamic, adaptable."}]
    if all(s in fixed for s in signs):
        return [{"name": "Musala Yoga (Nabhasa)", "type": "auspicious", "category": "Nabhasa",
                 "planets": [], "description": "All planets in fixed signs. Stubborn determination."}]
    if all(s in dual for s in signs):
        return [{"name": "Nala Yoga (Nabhasa)", "type": "auspicious", "category": "Nabhasa",
                 "planets": [], "description": "All planets in dual signs. Versatile, skilled."}]
    return []


def _nabhasa_dala(planets: list[dict]) -> list[dict]:
    kendra_check = {1, 4, 7, 10}
    benefic_names = {"Jupiter", "Venus", "Mercury"}
    malefic_names = {"Mars", "Saturn"}
    benefic_kendras = set()
    malefic_kendras = set()
    for p in planets:
        if p["house"] in kendra_check:
            if p["name"] in benefic_names:
                benefic_kendras.add(p["house"])
            if p["name"] in malefic_names:
                malefic_kendras.add(p["house"])
    yogas = []
    if len(benefic_kendras) >= 3:
        yogas.append({"name": "Mala Yoga (Nabhasa)", "type": "auspicious", "category": "Nabhasa",
                      "planets": [], "description": "Benefics in 3+ kendras. Garland of fortune."})
    if len(malefic_kendras) >= 3:
        yogas.append({"name": "Sarpa Yoga (Nabhasa)", "type": "challenging", "category": "Nabhasa",
                      "planets": [], "description": "Malefics in 3+ kendras. Obstacles in life."})
    return yogas


# --- Graha Malika ---

def _graha_malika(planets: list[dict]) -> list[dict]:
    classical = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
    occupied = {p["house"] for p in planets if p["name"] in classical}
    if not occupied:
        return []
    best_chain = 0
    best_start = 0
    for start in range(1, 13):
        chain = 0
        for offset in range(12):
            if _houses_from(start, offset) in occupied:
                chain += 1
            else:
                break
        if chain > best_chain:
            best_chain = chain
            best_start = start
    if best_chain >= 7:
        return [{"name": "Graha Malika Yoga (Full)", "type": "auspicious", "category": "Raja",
                 "planets": [], "description": f"All 7 planets in {best_chain} consecutive houses from H{best_start}."}]
    if best_chain >= 5:
        return [{"name": "Graha Malika Yoga (Partial)", "type": "auspicious", "category": "Special",
                 "planets": [], "description": f"{best_chain} consecutive houses occupied from H{best_start}."}]
    return []


# ──────────────────────────────────────────────
# Orchestrator: detect all yogas
# ──────────────────────────────────────────────

def _detect_yogas_internal(planets: list[dict], houses: list[dict]) -> list[dict]:
    """Detect all applicable yogas from adapted chart data."""
    yogas = []
    yogas.extend(_pancha_mahapurusha(planets))
    yogas.extend(_raja_yogas(planets, houses))
    yogas.extend(_gajakesari(planets))
    yogas.extend(_budhaditya(planets))
    yogas.extend(_chandra_mangala(planets))
    yogas.extend(_amala(planets))
    yogas.extend(_dhana_yogas(planets, houses))
    yogas.extend(_viparita_raja(planets, houses))
    yogas.extend(_neecha_bhanga(planets, houses))
    yogas.extend(_parivartana(planets, houses))
    yogas.extend(_saraswati(planets))
    yogas.extend(_kemadruma(planets))
    yogas.extend(_sunapha_anapha_durudhara(planets))
    yogas.extend(_adhi_yoga(planets))
    yogas.extend(_shakata(planets))
    yogas.extend(_kala_sarpa(planets))
    yogas.extend(_mahabhagya(planets, houses))
    # Doshas
    yogas.extend(_manglik_dosha(planets, houses))
    yogas.extend(_guru_chandal_dosha(planets))
    yogas.extend(_shrapit_dosha(planets))
    yogas.extend(_grahan_dosha(planets))
    yogas.extend(_pitri_dosha(planets, houses))
    yogas.extend(_angarak_dosha(planets))
    yogas.extend(_vish_dosha(planets))
    # Solar yogas
    yogas.extend(_vesi_vasi_ubhayachari(planets))
    # Kartari
    yogas.extend(_kartari_yogas(planets))
    # Nabhasa Sankhya
    yogas.extend(_sankhya_nabhasa(planets))
    # Named yogas
    yogas.extend(_lakshmi_yoga(planets, houses))
    yogas.extend(_gauri_yoga(planets))
    yogas.extend(_kalanidhi_yoga(planets))
    yogas.extend(_chamara_yoga(planets, houses))
    yogas.extend(_parvata_yoga(planets, houses))
    yogas.extend(_kahala_yoga(planets, houses))
    yogas.extend(_akhanda_samrajya(planets, houses))
    # Two-planet
    yogas.extend(_guru_mangala(planets))
    yogas.extend(_shani_mangala(planets))
    yogas.extend(_pravrajya(planets))
    # Daridra
    yogas.extend(_daridra_yogas(planets, houses))
    # Batch 2
    yogas.extend(_bheri_yoga(planets, houses))
    yogas.extend(_vasumathi_yoga(planets))
    yogas.extend(_srinatha_yoga(planets, houses))
    yogas.extend(_vidyut_yoga(planets, houses))
    yogas.extend(_pushti_yoga(planets, houses))
    yogas.extend(_parijata_yoga(planets, houses))
    # Batch 4
    yogas.extend(_pushkala_yoga(planets, houses))
    yogas.extend(_gandharva_yoga(planets, houses))
    yogas.extend(_bhrigu_mangala(planets))
    yogas.extend(_vargottama_yoga(planets, houses))
    # Batch 3
    yogas.extend(_chandra_guru(planets))
    yogas.extend(_chandra_shukra(planets))
    yogas.extend(_shukra_aditya(planets))
    yogas.extend(_guru_shani(planets))
    yogas.extend(_nabhasa_ashraya(planets))
    yogas.extend(_nabhasa_dala(planets))
    yogas.extend(_graha_malika(planets))

    # Sort: auspicious first, then by category
    category_order = {
        "Mahapurusha": 0, "Raja": 1, "Dhana": 2,
        "Benefic": 3, "Nabhasa": 4, "Special": 5,
        "Challenging": 6, "Dosha": 7,
    }
    yogas.sort(key=lambda y: (
        0 if y["type"] == "auspicious" else 1,
        category_order.get(y["category"], 9),
    ))

    return yogas


# ──────────────────────────────────────────────
# YOGA_META: yoga → dimension mapping
# ──────────────────────────────────────────────

YOGA_META: dict[str, dict] = {
    # Mahapurusha
    "Ruchaka Yoga": {"dims": ["execution", "authority"], "polarity": +1, "lord": "Mars"},
    "Bhadra Yoga": {"dims": ["analysis", "innovation"], "polarity": +1, "lord": "Mercury"},
    "Hamsa Yoga": {"dims": ["wisdom", "empathy"], "polarity": +1, "lord": "Jupiter"},
    "Malavya Yoga": {"dims": ["aesthetics", "empathy"], "polarity": +1, "lord": "Venus"},
    "Shasha Yoga": {"dims": ["restriction", "authority"], "polarity": +1, "lord": "Saturn"},
    # Raja
    "Yoga Karaka": {"dims": ["authority", "wisdom"], "polarity": +1, "lord": None},
    "Raja Yoga": {"dims": ["authority", "execution"], "polarity": +1, "lord": None},
    "Dharma Karma Adhipati Yoga (Parivartana)": {"dims": ["wisdom", "authority"], "polarity": +1, "lord": None},
    "Parivartana Yoga (Maha)": {"dims": ["authority", "wisdom"], "polarity": +1, "lord": None},
    "Chamara Yoga": {"dims": ["authority", "wisdom"], "polarity": +1, "lord": "Jupiter"},
    "Parvata Yoga": {"dims": ["authority", "aesthetics"], "polarity": +1, "lord": None},
    "Kahala Yoga": {"dims": ["execution", "wisdom"], "polarity": +1, "lord": None},
    "Akhanda Samrajya Yoga": {"dims": ["authority", "wisdom"], "polarity": +1, "lord": "Jupiter"},
    "Mahabhagya Yoga": {"dims": ["authority", "empathy"], "polarity": +1, "lord": None},
    "Adhi Yoga": {"dims": ["authority", "analysis"], "polarity": +1, "lord": None},
    "Srinatha Yoga": {"dims": ["authority", "aesthetics"], "polarity": +1, "lord": None},
    "Parijata Yoga": {"dims": ["authority", "wisdom"], "polarity": +1, "lord": None},
    "Graha Malika Yoga (Full)": {"dims": ["wisdom", "authority"], "polarity": +1, "lord": None},
    "Graha Malika Yoga (Partial)": {"dims": ["wisdom"], "polarity": +1, "lord": None},
    # Dhana
    "Dhana Yoga": {"dims": ["aesthetics", "authority"], "polarity": +1, "lord": None},
    "Chandra-Mangala Yoga": {"dims": ["execution", "empathy"], "polarity": +1, "lord": "Mars"},
    "Lakshmi Yoga": {"dims": ["aesthetics", "wisdom"], "polarity": +1, "lord": None},
    "Bheri Yoga": {"dims": ["aesthetics", "wisdom"], "polarity": +1, "lord": "Venus"},
    "Vasumathi Yoga": {"dims": ["aesthetics", "analysis"], "polarity": +1, "lord": None},
    "Vidyut Yoga": {"dims": ["innovation", "aesthetics"], "polarity": +1, "lord": None},
    "Pushkala Yoga": {"dims": ["aesthetics", "authority"], "polarity": +1, "lord": None},
    "Bhrigu-Mangala Yoga": {"dims": ["aesthetics", "execution"], "polarity": +1, "lord": "Venus"},
    # Benefic
    "Gajakesari Yoga": {"dims": ["empathy", "wisdom"], "polarity": +1, "lord": "Jupiter"},
    "Gajakesari Yoga (weakened)": {"dims": ["empathy", "wisdom"], "polarity": +1, "lord": "Jupiter"},
    "Budhaditya Yoga": {"dims": ["analysis", "authority"], "polarity": +1, "lord": "Mercury"},
    "Amala Yoga": {"dims": ["wisdom", "aesthetics"], "polarity": +1, "lord": None},
    "Saraswati Yoga": {"dims": ["analysis", "wisdom"], "polarity": +1, "lord": "Jupiter"},
    "Sunapha Yoga": {"dims": ["authority", "analysis"], "polarity": +1, "lord": None},
    "Anapha Yoga": {"dims": ["empathy", "aesthetics"], "polarity": +1, "lord": None},
    "Durudhara Yoga": {"dims": ["empathy", "analysis"], "polarity": +1, "lord": None},
    "Ubhayachari Yoga": {"dims": ["authority", "analysis"], "polarity": +1, "lord": None},
    "Vesi Yoga": {"dims": ["authority", "aesthetics"], "polarity": +1, "lord": None},
    "Vasi Yoga": {"dims": ["compression", "empathy"], "polarity": +1, "lord": None},
    "Guru-Mangala Yoga": {"dims": ["wisdom", "execution"], "polarity": +1, "lord": "Jupiter"},
    "Gauri Yoga": {"dims": ["empathy", "wisdom"], "polarity": +1, "lord": "Moon"},
    "Kalanidhi Yoga": {"dims": ["analysis", "aesthetics"], "polarity": +1, "lord": "Jupiter"},
    "Pushti Yoga": {"dims": ["empathy", "wisdom"], "polarity": +1, "lord": "Jupiter"},
    "Gandharva Yoga": {"dims": ["aesthetics", "wisdom"], "polarity": +1, "lord": None},
    "Chandra-Guru Yoga": {"dims": ["empathy", "wisdom"], "polarity": +1, "lord": "Jupiter"},
    "Chandra-Shukra Yoga": {"dims": ["empathy", "aesthetics"], "polarity": +1, "lord": "Venus"},
    "Shukra-Aditya Yoga": {"dims": ["aesthetics", "authority"], "polarity": +1, "lord": "Venus"},
    # Nabhasa
    "Gola Yoga": {"dims": ["compression"], "polarity": -1, "lord": None},
    "Yuga Yoga": {"dims": ["compression"], "polarity": -1, "lord": None},
    "Shula Yoga": {"dims": ["execution"], "polarity": +1, "lord": None},
    "Kedara Yoga": {"dims": ["restriction", "analysis"], "polarity": +1, "lord": None},
    "Pasha Yoga": {"dims": ["restriction"], "polarity": -1, "lord": None},
    "Dama Yoga": {"dims": ["innovation"], "polarity": +1, "lord": None},
    "Veena Yoga": {"dims": ["aesthetics", "innovation"], "polarity": +1, "lord": None},
    "Rajju Yoga (Nabhasa)": {"dims": ["innovation", "execution"], "polarity": +1, "lord": None},
    "Musala Yoga (Nabhasa)": {"dims": ["restriction", "authority"], "polarity": +1, "lord": None},
    "Nala Yoga (Nabhasa)": {"dims": ["analysis", "innovation"], "polarity": +1, "lord": None},
    "Mala Yoga (Nabhasa)": {"dims": ["aesthetics", "empathy"], "polarity": +1, "lord": None},
    "Sarpa Yoga (Nabhasa)": {"dims": ["restriction", "execution"], "polarity": -1, "lord": None},
    # Special
    "Viparita Raja Yoga": {"dims": ["innovation", "execution"], "polarity": +1, "lord": None},
    "Neecha Bhanga Raja Yoga": {"dims": ["compression", "wisdom"], "polarity": +1, "lord": None},
    "Parivartana Yoga (Dainya)": {"dims": ["compression", "restriction"], "polarity": -1, "lord": None},
    "Parivartana Yoga (Khala)": {"dims": ["restriction"], "polarity": -1, "lord": None},
    "Pravrajya Yoga": {"dims": ["compression", "wisdom"], "polarity": +1, "lord": None},
    "Vargottama Yoga": {"dims": ["authority", "wisdom"], "polarity": +1, "lord": None},
    "Guru-Shani Yoga": {"dims": ["wisdom", "restriction"], "polarity": +1, "lord": "Jupiter"},
    # Challenging
    "Kemadruma Yoga": {"dims": ["empathy", "restriction"], "polarity": -1, "lord": "Moon"},
    "Shakata Yoga": {"dims": ["wisdom", "aesthetics"], "polarity": -1, "lord": "Jupiter"},
    "Shani-Mangala Yoga": {"dims": ["execution", "restriction"], "polarity": -1, "lord": None},
    "Daridra Yoga": {"dims": ["aesthetics", "authority"], "polarity": -1, "lord": None},
    "Shukra-Aditya Yoga (combust)": {"dims": ["aesthetics"], "polarity": -1, "lord": "Venus"},
    # Dosha
    "Manglik Dosha": {"dims": ["execution"], "polarity": -1, "lord": "Mars"},
    "Manglik Dosha (cancelled)": {"dims": ["execution"], "polarity": +1, "lord": "Mars"},
    "Guru Chandal Dosha": {"dims": ["wisdom", "innovation"], "polarity": -1, "lord": "Jupiter"},
    "Shrapit Dosha": {"dims": ["restriction", "innovation"], "polarity": -1, "lord": "Saturn"},
    "Pitri Dosha": {"dims": ["authority"], "polarity": -1, "lord": "Sun"},
    "Angarak Dosha": {"dims": ["execution", "innovation"], "polarity": -1, "lord": "Mars"},
    "Vish Dosha": {"dims": ["empathy", "restriction"], "polarity": -1, "lord": "Moon"},
    "Vish Dosha (mitigated)": {"dims": ["empathy", "restriction"], "polarity": -1, "lord": "Moon"},
}

# Default effect for unknown yogas
_DEFAULT_EFFECTS: dict[str, str] = {
    "auspicious": "beneficial_combination",
    "challenging": "challenging_pattern",
}


def _yoga_effect(yoga: dict) -> str:
    """Derive an effect string from yoga meta or defaults."""
    name = yoga.get("name", "")
    # Try exact match first
    meta = YOGA_META.get(name)
    if meta:
        dims = meta["dims"]
        polarity = meta["polarity"]
        if polarity > 0:
            return "_".join(dims)
        return "restricted_" + "_".join(dims)

    # Try prefix match for variants (e.g., "Kala Sarpa Dosha (Ananta)")
    for key in YOGA_META:
        if name.startswith(key.split(" (")[0]) or key.startswith(name.split(" (")[0]):
            meta = YOGA_META[key]
            dims = meta["dims"]
            polarity = meta["polarity"]
            if polarity > 0:
                return "_".join(dims)
            return "restricted_" + "_".join(dims)

    # Grahan Dosha variants
    if "Grahan" in name:
        return "restricted_authority" if "Sun" in name else "restricted_empathy"

    # Papa/Shubha Kartari variants
    if "Papa Kartari" in name:
        return "restricted_authority"
    if "Shubha Kartari" in name:
        return "authority_empathy"

    # Default from type
    return _DEFAULT_EFFECTS.get(yoga.get("type", ""), "neutral")


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

def detect_yogas_full(
    positions: dict[str, dict],
    houses: list[dict],
    combustion: dict[str, bool],
) -> list[dict]:
    """Full yoga detection: adapt data -> detect -> add effect field.

    Returns list of yoga dicts with: name, type, category, planets, description, effect.
    """
    planets = _adapt_chart_data(positions, houses, combustion)
    yogas = _detect_yogas_internal(planets, houses)

    # Add effect field (backward compat with existing tests)
    for yoga in yogas:
        yoga["effect"] = _yoga_effect(yoga)

    return yogas


def compute_yoga_dimensions(yogas: list[dict]) -> dict:
    """Aggregate yoga effects into per-dimension scores.

    Returns: {
        "net": {dim: float},         # net score per dimension
        "volatility": {dim: float},  # std dev (conflict indicator)
        "conflicts": [str],          # dialectic dimension conflicts
    }
    """
    from collections import defaultdict
    dim_scores: dict[str, list[float]] = defaultdict(list)

    for yoga in yogas:
        name = yoga.get("name", "")
        # Find meta (exact or prefix match)
        meta = YOGA_META.get(name)
        if not meta:
            for key in YOGA_META:
                if name.startswith(key.split(" (")[0]) or key.startswith(name.split(" (")[0]):
                    meta = YOGA_META[key]
                    break

        if not meta:
            continue

        polarity = meta["polarity"]
        dims = meta["dims"]
        weight = 0.15 if len(dims) == 1 else 0.1
        for dim in dims:
            dim_scores[dim].append(polarity * weight)

    # Aggregate
    net: dict[str, float] = {}
    volatility: dict[str, float] = {}
    for dim, scores in dim_scores.items():
        total = sum(scores)
        net[dim] = max(-0.3, min(0.3, total))  # cap ±0.3
        if len(scores) > 1:
            mean = total / len(scores)
            var = sum((s - mean) ** 2 for s in scores) / len(scores)
            volatility[dim] = var ** 0.5
        else:
            volatility[dim] = 0.0

    # Detect dialectic conflicts: dimension pulled both ways
    conflicts = []
    for dim, scores in dim_scores.items():
        has_pos = any(s > 0 for s in scores)
        has_neg = any(s < 0 for s in scores)
        if has_pos and has_neg:
            conflicts.append(dim)

    return {
        "net": net,
        "volatility": volatility,
        "conflicts": conflicts,
    }
