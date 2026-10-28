"""
Natural language amount and description parser for expenses.
Supports Indian numbering shorthand (k, lakh, lac, crore), symbols (₹, Rs, INR),
and multi-expense splitting.
"""
import re
from typing import Optional, Tuple, List, Dict, Any


# Shorthand multipliers
MULTIPLIERS = {
    "k": 1_000.0,
    "thousand": 1_000.0,
    "lakh": 100_000.0,
    "lac": 100_000.0,
    "lakhs": 100_000.0,
    "lacs": 100_000.0,
    "l": 100_000.0,
    "crore": 10_000_000.0,
    "crores": 10_000_000.0,
    "cr": 10_000_000.0,
}

# Regex to find currency and amount
# Matches: ₹2,000 | Rs. 500 | 2.5k | 2 lakh | 1500 | 500/- | etc.
AMOUNT_PATTERN = re.compile(
    r"""
    (?P<prefix>(?:₹|rs\.?|inr)\s*)?
    (?P<number>\d+(?:,\d+)*(?:\.\d+)?)
    \s*
    (?P<unit>k|thousand|lakhs?|lacs?|crores?|cr|l)?
    (?P<suffix>/-)?
    (?!\w)
    """,
    re.IGNORECASE | re.VERBOSE
)

# Common filler phrases to strip from extracted descriptions
FILLER_WORDS = [
    r"^(?:i\s+)?(?:have\s+)?bought\s+(?:a\s+|an\s+|the\s+|some\s+)?",
    r"^(?:i\s+)?(?:have\s+)?paid\s+(?:for\s+|to\s+)?",
    r"^(?:i\s+)?(?:have\s+)?spent\s+(?:on\s+)?",
    r"^(?:i\s+)?(?:have\s+)?purchased\s+",
    r"^(?:i\s+)?ordered\s+(?:a\s+|an\s+|the\s+|some\s+)?",
    r"^(?:i\s+)?gave\s+(?:to\s+)?",
    r"\bworth\s+of\b",
    r"\bworth\b",
]


def normalize_number(num_str: str) -> float:
    """Removes commas and parses float."""
    clean = num_str.replace(",", "").strip()
    return float(clean)


def extract_amount_value(match: re.Match) -> Tuple[float, str]:
    """Calculates numeric float value from regex match and returns (value, raw_str)."""
    raw_str = match.group(0).strip()
    num = normalize_number(match.group("number"))
    unit = match.group("unit")
    
    multiplier = 1.0
    if unit:
        unit_lower = unit.lower()
        multiplier = MULTIPLIERS.get(unit_lower, 1.0)
    
    value = round(num * multiplier, 2)
    return value, raw_str


def clean_description(desc: str) -> str:
    """Cleans up leftover text after removing the amount."""
    text = desc.strip()
    
    # Remove leading/trailing punctuation and symbols
    text = re.sub(r"^[,\-–—:\.\s]+|[,\-–—:\.\s]+$", "", text)
    
    # Remove leading noise verbs ("Bought Nike shoes for" -> "Nike shoes")
    for pattern in FILLER_WORDS:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE).strip()

    # Clean multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    
    # Remove trailing/leading prepositions again if left exposed
    text = re.sub(r"^(?:for|to|on|at|in|of)\s+", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"\s+(?:for|to|on|at|in|of)$", "", text, flags=re.IGNORECASE).strip()
    
    # Capitalize first letter of each word if all lower
    if text and text.islower():
        text = text.title()
    elif not text:
        text = "Expense"
        
    return text


def parse_single_expense(text: str) -> Optional[Tuple[float, str, str]]:
    """
    Parses a single expense clause.
    Returns: (amount, description, raw_amount_str) or None if no valid amount found.
    """
    text = text.strip()
    if not text:
        return None

    # Find all amount matches
    matches = list(AMOUNT_PATTERN.finditer(text))
    if not matches:
        return None

    # Filter out empty matches (where number is absent)
    valid_matches = [m for m in matches if m.group("number")]
    if not valid_matches:
        return None

    # Pick the best match (favor matches with currency prefix or unit, or first valid)
    best_match = None
    for m in valid_matches:
        if m.group("prefix") or m.group("unit"):
            best_match = m
            break
    if not best_match:
        best_match = valid_matches[0]

    amount, raw_amount_str = extract_amount_value(best_match)
    if amount <= 0:
        return None

    # Remove amount from text to get description
    start, end = best_match.span()
    desc_part = text[:start] + " " + text[end:]
    description = clean_description(desc_part)

    return amount, description, raw_amount_str


def has_amount(text: str) -> bool:
    """Checks if a string fragment contains a recognizable expense amount."""
    matches = list(AMOUNT_PATTERN.finditer(text))
    return any(bool(m.group("number")) for m in matches)


def split_multi_expense_input(raw_text: str) -> List[str]:
    """
    Splits multi-expense inputs only when separated clauses each contain amounts.
    Examples:
      - "500 petrol, 200 coffee, 1200 electricity bill" -> splits into 3
      - "Milk, eggs and vegetables 250" -> DOES NOT split because "Milk" and "eggs" have no amount
      - "2k biryani and 500 petrol" -> splits into 2
    """
    # First split by newline or semicolon
    lines = [line.strip() for line in re.split(r"[\n;]+", raw_text) if line.strip()]
    segments = []

    for line in lines:
        # Check if line has multiple amounts separated by commas
        # Replace commas between digits with a placeholder first to preserve numbers like 2,000
        protected = re.sub(r"(\d),(\d)", r"\1__COMMA__\2", line)
        comma_parts = [p.replace("__COMMA__", ",").strip() for p in protected.split(",")]
        
        # Only split on comma if at least 2 parts contain amounts
        parts_with_amounts = [p for p in comma_parts if has_amount(p)]
        if len(comma_parts) > 1 and len(parts_with_amounts) >= 2 and len(parts_with_amounts) == len(comma_parts):
            # Each comma-separated part has its own amount
            for part in comma_parts:
                and_parts = re.split(r"\s+and\s+", part, flags=re.IGNORECASE)
                if len(and_parts) > 1 and all(has_amount(p) for p in and_parts):
                    segments.extend([p.strip() for p in and_parts if p.strip()])
                else:
                    segments.append(part)
        else:
            # Check for " and " separating multiple expenses with amounts: e.g. "2k biryani and 500 petrol"
            and_parts = re.split(r"\s+and\s+", line, flags=re.IGNORECASE)
            if len(and_parts) > 1 and all(has_amount(p) for p in and_parts):
                segments.extend([p.strip() for p in and_parts if p.strip()])
            else:
                segments.append(line)

    return segments


def parse_natural_language_expenses(raw_text: str) -> List[Dict[str, Any]]:
    """
    Main entry point for parsing natural language expenses.
    Handles single entries or multiple entries.
    Returns list of dicts with:
      - 'amount': float
      - 'description': str
      - 'raw_amount_str': str
      - 'source_text': str
    """
    if not raw_text or not raw_text.strip():
        return []

    segments = split_multi_expense_input(raw_text)
    results = []

    for seg in segments:
        parsed = parse_single_expense(seg)
        if parsed:
            amount, desc, raw_str = parsed
            results.append({
                "amount": amount,
                "description": desc,
                "raw_amount_str": raw_str,
                "source_text": seg.strip(),
            })

    # If segments didn't yield anything but text has an amount, fallback to full text
    if not results:
        parsed = parse_single_expense(raw_text)
        if parsed:
            amount, desc, raw_str = parsed
            results.append({
                "amount": amount,
                "description": desc,
                "raw_amount_str": raw_str,
                "source_text": raw_text.strip(),
            })

    return results
