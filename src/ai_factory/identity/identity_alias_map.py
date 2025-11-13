"""
Identity Alias Map - v4.1.0
Semantic clustering for identity memory recall
"""

# Static alias dictionary - maps semantic concepts to memory keys
IDENTITY_ALIAS_MAP = {
    "hometown": ["village", "birthplace", "origin", "home", "where from", "my place", "home town", "home place"],
    "village": ["hometown", "origin", "home town", "where from", "my place", "birth village"],
    "birthplace": ["origin", "birth town", "where born", "birth place", "born in", "birth location"],
    "country": ["nation", "nationality", "from which country", "home country"],
    "city": ["town", "urban area", "municipality"],
    "profession": ["job", "work", "career", "what do I do", "occupation", "employment"],
    "favorite_color": ["color preference", "fav color", "preferred color", "color choice"],
    "favorite_food": ["food preference", "fav food", "preferred food", "food choice"],
    "favorite_drink": ["drink preference", "fav drink", "preferred drink", "beverage", "favorite beverage"],
    "name": ["full name", "my name", "what am I called"],
    "creator": ["who made me", "who created me", "my maker"],
    "birthdate": ["when born", "birth date", "date of birth", "birthday", "when was I born"],
}

# Common synonym patterns for auto-generation
SYNONYM_PATTERNS = {
    "favorite": ["fav", "preferred", "choice", "preference"],
    "home": ["hometown", "origin", "where from"],
    "birth": ["born", "birth place", "origin"],
    "work": ["job", "career", "occupation", "profession"],
    "drink": ["beverage"],
    "food": ["meal", "dish"],
    "color": ["colour"],
}

# Auto-generated aliases storage (populated at runtime)
AUTO_GENERATED_ALIASES = {}


def register_auto_alias(key: str, value: str = None):
    """
    Auto-generate aliases for a memory key.
    
    Args:
        key: The memory key (e.g., "favorite_drink")
        value: Optional value for context-aware aliasing
    
    Returns:
        List of generated aliases
    """
    if key in AUTO_GENERATED_ALIASES:
        return AUTO_GENERATED_ALIASES[key]
    
    aliases = set()
    
    # Split by underscore
    parts = key.split("_")
    
    # Add full key variants
    aliases.add(key)
    aliases.add(key.replace("_", " "))
    
    # Add each part individually
    for part in parts:
        aliases.add(part)
        
        # Add plural/singular
        if part.endswith("s"):
            aliases.add(part[:-1])
        else:
            aliases.add(part + "s")
        
        # Add synonyms
        for base, synonyms in SYNONYM_PATTERNS.items():
            if part.lower() == base:
                aliases.update(synonyms)
                for syn in synonyms:
                    # Add with other parts
                    for other_part in parts:
                        if other_part != part:
                            aliases.add(f"{syn} {other_part}")
                            aliases.add(f"{syn}_{other_part}")
    
    # Combine parts in different ways
    if len(parts) == 2:
        # e.g., "favorite_drink" -> "fav drink", "drink preference"
        for syn1 in SYNONYM_PATTERNS.get(parts[0], [parts[0]]):
            for syn2 in SYNONYM_PATTERNS.get(parts[1], [parts[1]]):
                aliases.add(f"{syn1} {syn2}")
                aliases.add(f"{syn2} {syn1}")  # reversed
    
    # Store and return
    AUTO_GENERATED_ALIASES[key] = list(aliases)
    return list(aliases)


def get_all_aliases_for_key(key: str) -> list:
    """
    Get all aliases (static + auto-generated) for a memory key.
    
    Args:
        key: The memory key
    
    Returns:
        List of all possible aliases
    """
    aliases = set()
    
    # Add static aliases
    if key in IDENTITY_ALIAS_MAP:
        aliases.update(IDENTITY_ALIAS_MAP[key])
    
    # Check reverse lookup (if key is an alias of another key)
    for main_key, alias_list in IDENTITY_ALIAS_MAP.items():
        if key in alias_list:
            aliases.add(main_key)
            aliases.update(alias_list)
    
    # Add auto-generated aliases
    if key in AUTO_GENERATED_ALIASES:
        aliases.update(AUTO_GENERATED_ALIASES[key])
    else:
        # Generate on-the-fly
        auto_aliases = register_auto_alias(key)
        aliases.update(auto_aliases)
    
    return list(aliases)


def find_best_match(query_text: str) -> str:
    """
    Find the best matching memory key from a query text.
    
    Args:
        query_text: User's query text
    
    Returns:
        Best matching key or None
    """
    import re
    
    # Normalize query
    normalized = query_text.lower().strip()
    normalized = re.sub(r'[^\w\s]', '', normalized)
    
    # Check all keys and their aliases
    all_keys = set(IDENTITY_ALIAS_MAP.keys()) | set(AUTO_GENERATED_ALIASES.keys())
    
    best_match = None
    best_score = 0
    
    for key in all_keys:
        aliases = get_all_aliases_for_key(key)
        
        for alias in aliases:
            alias_normalized = alias.lower().strip()
            
            # Exact match
            if alias_normalized == normalized:
                return key
            
            # Partial match scoring
            if alias_normalized in normalized or normalized in alias_normalized:
                score = len(alias_normalized)
                if score > best_score:
                    best_score = score
                    best_match = key
    
    return best_match

