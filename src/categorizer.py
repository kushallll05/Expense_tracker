"""
Hybrid Categorization Engine.
Layer 1: Rule-based classifier (keywords, merchants, Indian context, fuzzy matching).
Layer 2: Local language model (Ollama) with structured JSON output and strict validation.
Layer 3: Confidence scoring and ambiguity detection.
Layer 4: Persistent user learning / correction mappings with highest precedence.
"""
import re
import json
import logging
from typing import Optional, Dict, Any, Tuple
import requests
from src.config import (
    CATEGORIES,
    EXPENSE_CATEGORIES,
    ALL_CATEGORIES,
    HIGH_CONFIDENCE_THRESHOLD,
    MEDIUM_CONFIDENCE_THRESHOLD,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT_SECONDS,
)
from src.models import ParsedExpense, LearnedMapping
from src.database import Database

logger = logging.getLogger(__name__)

# ==================== LAYER 1: RULE-BASED DICTIONARIES ====================

MERCHANT_RULES = {
    # Food & Delivery
    "swiggy": ("Food", 0.95),
    "zomato": ("Food", 0.95),
    "eatclub": ("Food", 0.95),
    "mcdonalds": ("Food", 0.95),
    "dominos": ("Food", 0.95),
    "pizza hut": ("Food", 0.95),
    "starbucks": ("Food", 0.95),
    "kfc": ("Food", 0.95),
    "burger king": ("Food", 0.95),
    "subway": ("Food", 0.95),
    "haldiram": ("Food", 0.95),
    "chai point": ("Food", 0.95),
    "chaayos": ("Food", 0.95),
    "behrouz": ("Food", 0.95),
    "faasos": ("Food", 0.95),

    # Shopping
    "amazon": ("Shopping", 0.90),
    "flipkart": ("Shopping", 0.90),
    "myntra": ("Shopping", 0.95),
    "meesho": ("Shopping", 0.90),
    "ajio": ("Shopping", 0.95),
    "nykaa": ("Shopping", 0.95),
    "zara": ("Shopping", 0.95),
    "h&m": ("Shopping", 0.95),
    "uniqlo": ("Shopping", 0.95),
    "croma": ("Shopping", 0.90),
    "reliance digital": ("Shopping", 0.90),
    "nike": ("Shopping", 0.95),
    "adidas": ("Shopping", 0.95),
    "puma": ("Shopping", 0.95),
    "decathlon": ("Shopping", 0.90),
    "ikea": ("Shopping", 0.90),

    # Transport
    "uber": ("Transport", 0.95),
    "ola": ("Transport", 0.95),
    "rapido": ("Transport", 0.95),
    "irctc": ("Transport", 0.95),
    "redbus": ("Transport", 0.95),
    "makemytrip": ("Transport", 0.85),
    "indigo": ("Transport", 0.95),
    "air india": ("Transport", 0.95),
    "fastag": ("Transport", 0.95),
    "hp petrol": ("Transport", 0.95),
    "indian oil": ("Transport", 0.95),
    "bharat petroleum": ("Transport", 0.95),
    "bpcl": ("Transport", 0.95),
    "iocl": ("Transport", 0.95),

    # Bills & Utilities
    "airtel": ("Bills", 0.90),
    "jio": ("Bills", 0.90),
    "vodafone": ("Bills", 0.90),
    "vi": ("Bills", 0.85),
    "tatasky": ("Bills", 0.95),
    "tata play": ("Bills", 0.95),
    "bescom": ("Bills", 0.95),
    "tneb": ("Bills", 0.95),
    "mseb": ("Bills", 0.95),
    "adani electricity": ("Bills", 0.95),
    "indane": ("Bills", 0.95),
    "hp gas": ("Bills", 0.95),
    "bharat gas": ("Bills", 0.95),

    # Groceries
    "blinkit": ("Groceries", 0.95),
    "zepto": ("Groceries", 0.90),
    "instamart": ("Groceries", 0.95),
    "bigbasket": ("Groceries", 0.95),
    "dmart": ("Groceries", 0.95),
    "reliance fresh": ("Groceries", 0.95),
    "nature's basket": ("Groceries", 0.95),
    "spencer's": ("Groceries", 0.95),

    # Education
    "udemy": ("Education", 0.95),
    "coursera": ("Education", 0.95),
    "edx": ("Education", 0.95),
    "unacademy": ("Education", 0.95),
    "byjus": ("Education", 0.95),
    "skillshare": ("Education", 0.95),

    # Entertainment
    "netflix": ("Entertainment", 0.95),
    "prime video": ("Entertainment", 0.95),
    "hotstar": ("Entertainment", 0.95),
    "disney+": ("Entertainment", 0.95),
    "spotify": ("Entertainment", 0.95),
    "pvr": ("Entertainment", 0.95),
    "inox": ("Entertainment", 0.95),
    "bookmyshow": ("Entertainment", 0.95),
    "cinepolis": ("Entertainment", 0.95),
    "steam": ("Entertainment", 0.95),
    "playstation": ("Entertainment", 0.95),

    # Health
    "apollo": ("Health", 0.95),
    "pharmeasy": ("Health", 0.95),
    "1mg": ("Health", 0.95),
    "tata 1mg": ("Health", 0.95),
    "netmeds": ("Health", 0.95),
    "medplus": ("Health", 0.95),
    "cult.fit": ("Health", 0.90),
    "cult fit": ("Health", 0.90),

    # Investment
    "zerodha": ("Investment", 0.95),
    "groww": ("Investment", 0.95),
    "upstox": ("Investment", 0.95),
    "coinbase": ("Investment", 0.95),
    "wazirx": ("Investment", 0.95),
    "kuvera": ("Investment", 0.95),
}

KEYWORD_RULES = {
    "Food": [
        "biryani", "dosa", "idli", "chai", "tea", "coffee", "latte", "cappuccino",
        "samosa", "thali", "paneer", "naan", "roti", "paratha", "curry", "pizza",
        "burger", "sandwich", "shawarma", "momo", "momos", "pasta", "noodles",
        "kebab", "tandoori", "chicken", "mutton", "fish fry", "dessert", "ice cream",
        "cake", "pastry", "bakery", "restaurant", "cafe", "dhaba", "dinner", "lunch",
        "breakfast", "brunch", "snack", "snacks", "food", "meal", "buffet", "sweets",
        "mithai", "rasgulla", "gulab jamun", "vada", "pav bhaji", "bhel puri", "pani puri",
    ],
    "Shopping": [
        "shoes", "shoe", "sneakers", "boots", "sandals", "slippers", "chappal",
        "clothes", "clothing", "shirt", "t-shirt", "tshirt", "jeans", "trousers",
        "pants", "dress", "saree", "kurta", "kurti", "jacket", "hoodie", "watch",
        "sunglasses", "spectacles", "glasses", "bag", "backpack", "handbag", "wallet",
        "belt", "laptop", "mobile", "phone", "iphone", "ipad", "tablet", "headphone",
        "earphones", "earbuds", "airpods", "charger", "gadget", "keyboard", "mouse",
        "monitor", "tv", "furniture", "sofa", "bed", "mattress", "curtains", "jewellery",
        "gold ring", "earrings", "necklace", "shopping", "apparel",
    ],
    "Transport": [
        "petrol", "diesel", "fuel", "cng", "cab", "taxi", "ride", "auto", "rickshaw",
        "metro", "train", "flight", "airfare", "airline", "bus", "bus fare", "parking",
        "toll", "tollgate", "fastag", "scooter", "bike", "mechanic", "servicing",
        "car wash", "puncture", "tyre", "tire", "oil change", "driver", "transport",
        "commute", "fare",
    ],
    "Bills": [
        "electricity", "power", "current bill", "water bill", "gas bill", "cylinder",
        "broadband", "wifi", "internet", "dth", "cable", "recharge", "mobile recharge",
        "phone bill", "rent", "house rent", "maintenance", "society fee", "piped gas",
        "utility", "utilities", "property tax", "bill",
    ],
    "Groceries": [
        "milk", "eggs", "egg", "bread", "butter", "cheese", "curd", "yogurt", "paneer",
        "vegetables", "vegetable", "veggies", "sabzi", "sabji", "fruits", "fruit",
        "apple", "banana", "mango", "orange", "potato", "onion", "tomato", "ginger",
        "garlic", "atta", "flour", "rice", "dal", "pulses", "oil", "cooking oil", "ghee",
        "spices", "masala", "salt", "sugar", "tea powder", "coffee beans", "provisions",
        "grocery", "groceries", "supermarket", "kirana", "ration",
    ],
    "Education": [
        "course", "tutorial", "books", "book", "textbook", "novel", "python", "coding",
        "tuition", "coaching", "college", "school", "fees", "fee", "exam", "certification",
        "certificate", "class", "classes", "workshop", "stationery", "notebook", "pen",
        "pencil", "pencil box", "library", "admission", "study",
    ],
    "Entertainment": [
        "movie", "cinema", "theatre", "theater", "ticket", "tickets", "show",
        "concert", "music festival", "carnival", "circus", "amusement park",
        "bowling", "club", "party", "pub", "brewery", "beer", "cocktails",
        "ott", "streaming", "subscription", "video game", "gaming", "playstation",
        "game", "board game", "match", "ipl", "stadium",
    ],
    "Health": [
        "doctor", "consultation", "clinic", "hospital", "physician", "pediatrician",
        "medicine", "medicines", "pills", "syrup", "tablet", "pharmacy", "medical",
        "chemist", "test", "blood test", "x-ray", "scan", "mri", "dentist", "dental",
        "eye test", "physiotherapy", "gym", "fitness", "yoga", "protein", "whey",
        "vitamins", "supplements", "bandage", "first aid", "health", "checkup",
    ],
    "Personal Care": [
        "haircut", "salon", "parlour", "barber", "spa", "facial", "shave", "beard trim",
        "massage", "pedicure", "manicure", "waxing", "makeup", "cosmetics", "skincare",
        "sunscreen", "moisturizer", "perfume", "deodorant", "cologne", "shampoo",
        "conditioner", "soap", "facewash", "grooming", "hair color",
    ],
    "Investment": [
        "mutual fund", "sip", "stocks", "shares", "equity", "crypto", "bitcoin",
        "ethereum", "gold", "silver", "fixed deposit", "fd", "rd", "ppf", "nps",
        "epf", "bonds", "investment", "trading",
    ],
    "Salary": [
        "salary", "paycheck", "wages", "bonus", "incentive", "freelance", "stipend",
        "client payment", "dividend", "interest credited", "income",
    ],
}


class Categorizer:
    def __init__(self, db: Optional[Database] = None, use_ollama: bool = True):
        self.db = db
        self.use_ollama = use_ollama

    def _check_learned_mappings(self, description: str) -> Optional[Tuple[str, float, str]]:
        """
        Layer 4: Checks persistent user corrections.
        Returns (category, confidence, merchant) or None.
        """
        if not self.db:
            return None

        norm = description.strip().lower()
        # Direct match
        mapping = self.db.get_learned_mapping(norm)
        if mapping:
            return mapping.category, 1.0, mapping.merchant

        # Word-level containment check for learned phrases
        all_mappings = self.db.get_all_learned_mappings()
        for m in all_mappings:
            if m.normalized_description in norm or norm in m.normalized_description:
                return m.category, 0.98, m.merchant

        return None

    def _classify_rules(self, text: str) -> Tuple[str, float, Optional[str], Optional[str]]:
        """
        Layer 1: Rule-based classification based on keywords and merchants.
        Returns (category, confidence, merchant, match_reason).
        """
        norm_text = text.lower()
        words = set(re.findall(r"\b\w+\b", norm_text))

        # Check Merchant Rules First
        for merchant, (cat, conf) in MERCHANT_RULES.items():
            # Exact boundary match for merchant
            if re.search(rf"\b{re.escape(merchant)}\b", norm_text):
                return cat, conf, merchant.title(), f"Matched known merchant: {merchant.title()}"

        # Check keyword matches with weighting
        best_category = "Other"
        highest_score = 0.0
        best_reason = None

        # Give priority to specific multi-word phrases first
        for cat, keywords in KEYWORD_RULES.items():
            for kw in keywords:
                if " " in kw and kw in norm_text:
                    score = 0.90
                    if score > highest_score:
                        highest_score = score
                        best_category = cat
                        best_reason = f"Matched phrase '{kw}' in {cat}"

        # If no multi-word matched, check single words
        if highest_score < 0.8:
            category_counts: Dict[str, int] = {}
            for cat, keywords in KEYWORD_RULES.items():
                for kw in keywords:
                    if kw in words:
                        category_counts[cat] = category_counts.get(cat, 0) + 1

            if category_counts:
                # Find category with most hits
                top_cat = max(category_counts, key=category_counts.get)
                hits = category_counts[top_cat]
                # If only 1 hit, confidence is 0.85; if multiple hits, confidence is 0.92
                conf = 0.92 if hits > 1 else 0.85
                return top_cat, conf, None, f"Matched keyword(s) for {top_cat}"

        if highest_score > 0:
            return best_category, highest_score, None, best_reason

        # Default fallback
        return "Other", 0.30, None, "No confident rule matched"

    def _query_ollama(self, description: str, amount: float) -> Optional[Dict[str, Any]]:
        """
        Layer 2: Local language model inference via Ollama.
        Prompt asks for strict JSON output with validated categories.
        """
        if not self.use_ollama:
            return None

        prompt = f"""
You are a financial transaction categorization assistant.
Categorize the following transaction into one of these strict categories:
{json.dumps(ALL_CATEGORIES)}

Transaction Description: "{description}"
Amount: {amount} INR

Respond ONLY with a valid JSON object in this exact schema without any markdown formatting or commentary:
{{
  "category": "<one of the valid categories listed above>",
  "transaction_type": "expense",
  "confidence": <float between 0.0 and 1.0>,
  "merchant": "<merchant name if identified or null>",
  "reasoning": "<brief one sentence explanation>"
}}
"""

        try:
            url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate"
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 128,
                }
            }
            resp = requests.post(url, json=payload, timeout=OLLAMA_TIMEOUT_SECONDS)
            if resp.status_code == 200:
                data = resp.json()
                raw_response = data.get("response", "").strip()
                # Extract JSON block if surrounded by ```json ... ```
                json_match = re.search(r"\{.*\}", raw_response, re.DOTALL)
                if json_match:
                    parsed_json = json.loads(json_match.group(0))
                    cat = parsed_json.get("category")
                    # Validate category is in allowed list
                    if cat in ALL_CATEGORIES:
                        return {
                            "category": cat,
                            "transaction_type": parsed_json.get("transaction_type", "expense"),
                            "confidence": min(max(float(parsed_json.get("confidence", 0.8)), 0.0), 1.0),
                            "merchant": parsed_json.get("merchant"),
                            "reasoning": parsed_json.get("reasoning", "Classified by local LLM"),
                        }
        except Exception as e:
            logger.debug("Ollama categorization unavailable: %s", e)
            return None

        return None

    def categorize(self, description: str, amount: float, raw_amount_str: Optional[str] = None, source_text: Optional[str] = None) -> ParsedExpense:
        """
        Orchestrates hybrid categorization across all 4 layers:
        1. User corrections (Layer 4)
        2. Rule-based classifier (Layer 1)
        3. Local LLM via Ollama (Layer 2) if rule confidence < threshold
        4. Confidence & Ambiguity determination (Layer 3)
        """
        clean_desc = description.strip()

        # 1. Check Learned User Mappings (Layer 4)
        learned = self._check_learned_mappings(clean_desc)
        if learned:
            cat, conf, merch = learned
            return ParsedExpense(
                amount=amount,
                description=clean_desc,
                category=cat,
                confidence=conf,
                transaction_type="income" if cat == "Salary" else "expense",
                merchant=merch,
                source_text=source_text or clean_desc,
                raw_amount_str=raw_amount_str,
                is_ambiguous=False,
                reasoning="Matched learned user correction",
            )

        # 2. Check Rule-Based Classifier (Layer 1)
        rule_cat, rule_conf, rule_merch, rule_reason = self._classify_rules(clean_desc)

        # If rule confidence is high (>= 0.75), accept immediately
        if rule_conf >= HIGH_CONFIDENCE_THRESHOLD:
            return ParsedExpense(
                amount=amount,
                description=clean_desc,
                category=rule_cat,
                confidence=rule_conf,
                transaction_type="income" if rule_cat == "Salary" else "expense",
                merchant=rule_merch,
                source_text=source_text or clean_desc,
                raw_amount_str=raw_amount_str,
                is_ambiguous=False,
                reasoning=rule_reason,
            )

        # 3. Fallback to Local LLM (Layer 2) for ambiguous or unfamiliar terms
        llm_result = self._query_ollama(clean_desc, amount)
        if llm_result:
            llm_cat = llm_result["category"]
            llm_conf = llm_result["confidence"]
            return ParsedExpense(
                amount=amount,
                description=clean_desc,
                category=llm_cat,
                confidence=llm_conf,
                transaction_type=llm_result.get("transaction_type", "expense"),
                merchant=llm_result.get("merchant") or rule_merch,
                source_text=source_text or clean_desc,
                raw_amount_str=raw_amount_str,
                is_ambiguous=(llm_conf < HIGH_CONFIDENCE_THRESHOLD),
                reasoning=llm_result.get("reasoning", "Classified by local LLM"),
            )

        # 4. Final Rule Fallback
        is_ambiguous = rule_conf < HIGH_CONFIDENCE_THRESHOLD
        return ParsedExpense(
            amount=amount,
            description=clean_desc,
            category=rule_cat,
            confidence=rule_conf,
            transaction_type="income" if rule_cat == "Salary" else "expense",
            merchant=rule_merch,
            source_text=source_text or clean_desc,
            raw_amount_str=raw_amount_str,
            is_ambiguous=is_ambiguous,
            reasoning=rule_reason or "Low confidence match",
        )
