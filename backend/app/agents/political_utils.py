"""Shared helpers for political studies analysis."""

from typing import List, Dict, Any


TOPIC_KEYWORDS = {
    "energy": ["oil", "gas", "energy", "petroleum", "opec", "fuel", "lng", "pipeline"],
    "geopolitics": ["conflict", "war", "diplomacy", "sanctions", "alliance", "treaty", "geopolitical"],
    "economics": ["trade", "tariff", "gdp", "inflation", "recession", "market", "growth"],
    "technology": ["ai", "cyber", "technology", "digital", "semiconductor", "tech"],
    "security": ["defense", "military", "security", "terrorism", "nuclear", "missile"],
    "climate": ["climate", "carbon", "emissions", "sustainability", "environment"],
    "governance": ["democracy", "election", "policy", "governance", "regulation", "parliament"],
    "finance": ["banking", "finance", "investment", "currency", "debt", "rates"],
    "humanitarian": ["refugee", "humanitarian", "aid", "displacement", "crisis"],
    "protest": ["protest", "demonstration", "strike", "unrest", "riot"]
}

REGION_KEYWORDS = {
    "middle_east": ["middle east", "gulf", "saudi", "iran", "iraq", "syria", "lebanon",
                    "jordan", "israel", "palestine", "uae", "qatar", "kuwait", "bahrain",
                    "oman", "yemen", "mena", "gcc"],
    "europe": ["eu", "europe", "european", "nato", "uk", "britain", "germany", "france",
               "italy", "spain", "poland", "ukraine"],
    "asia_pacific": ["china", "japan", "korea", "asean", "india", "pacific", "asia",
                      "taiwan", "indonesia", "vietnam", "thailand"],
    "americas": ["us", "usa", "america", "canada", "mexico", "brazil", "latin america"],
    "africa": ["africa", "african", "sub-saharan", "north africa", "south africa"],
    "russia_eurasia": ["russia", "russian", "eurasia", "central asia", "kazakhstan",
                        "belarus", "caucasus"]
}


def extract_topics(text: str) -> List[str]:
    """Extract topic labels from text based on keyword matches."""
    text_lower = (text or "").lower()
    topics: List[str] = []

    for topic, keywords in TOPIC_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                if topic not in topics:
                    topics.append(topic)
                break

    return topics


def extract_regions(text: str) -> List[str]:
    """Extract region labels from text based on keyword matches."""
    text_lower = (text or "").lower()
    regions: List[str] = []

    for region, keywords in REGION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                region_name = region.replace("_", " ").title()
                if region_name not in regions:
                    regions.append(region_name)
                break

    return regions


def normalize_probabilities(
    items: List[Dict[str, Any]],
    key: str = "probability"
) -> List[Dict[str, Any]]:
    """Normalize probability fields in a list of dicts."""
    total = sum(max(0.0, float(item.get(key, 0.0))) for item in items)
    if total <= 0:
        return items

    for item in items:
        item[key] = float(item.get(key, 0.0)) / total

    return items


def clamp(value: float, min_value: float, max_value: float) -> float:
    """Clamp a numeric value to a range."""
    return max(min_value, min(max_value, value))


def is_election_related(text: str) -> bool:
    """Check if scenario text is election-related."""
    text_lower = (text or "").lower()
    election_terms = ["election", "vote", "ballot", "referendum", "campaign", "parliament", "poll"]
    return any(term in text_lower for term in election_terms)


def scenario_templates(scenario: str) -> List[str]:
    """Select scenario templates based on scenario content."""
    scenario_lower = (scenario or "").lower()

    if any(term in scenario_lower for term in ["election", "vote", "ballot", "referendum", "campaign"]):
        return [
            "Incumbent advantage holds",
            "Opposition gains ground",
            "Fragmented or disputed outcome"
        ]

    if any(term in scenario_lower for term in ["policy", "regulation", "law", "sanction", "treaty"]):
        return [
            "Policy accelerates",
            "Policy stalls",
            "Policy reverses"
        ]

    if any(term in scenario_lower for term in ["conflict", "war", "tension", "military", "attack", "terror"]):
        return [
            "Escalation",
            "Stalemate",
            "De-escalation"
        ]

    if any(term in scenario_lower for term in ["oil", "energy", "gas", "price", "market"]):
        return [
            "Supply tightening",
            "Baseline supply",
            "Supply easing"
        ]

    return [
        "Downside risk",
        "Baseline trajectory",
        "Upside opportunity"
    ]
