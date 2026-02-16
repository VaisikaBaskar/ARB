# backend/ai_cook/intent_parser.py
# Rule-based NLP for AI Cooking Assistant
# ISOLATED MODULE - NO DB Access

import re

# Predefined Knowledge Base (Extensible)
KNOWN_DISHES = [
    "chicken biryani", "vegetable pulao", "veg pulao", "egg fried rice",
    "butter chicken", "paneer tikka", "dal makhani", "pasta alfredo",
    "margherita pizza", "grilled cheese", "tomato soup", "chicken curry",
    "fish curry", "vegetable soup", "chocolate cake", "omelette",
    "scrambled eggs", "fruit salad", "smoothie"
]

NUMBER_MAP = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
}

# Common variations mapping
SYNONYM_MAP = {
    "biriyani": "biryani",
    "pulav": "pulao",
    "pillau": "pulao",
    "chiken": "chicken",
    "friedrice": "fried rice",
    "omlet": "omelette",
    "omlette": "omelette"
}

def parse_intent(raw_text):
    """
    Analyzes natural language input to extract cooking intent.
    Input: "I want to cook chicken biryani for 2 people"
    Output: {"dish": "chicken biryani", "servings": 2}
    """
    if not raw_text or not isinstance(raw_text, str):
        return {"dish": None, "servings": 1}

    # Normalize Text
    text = raw_text.lower().strip()
    
    # Apply Synonyms (Simple Replace)
    for bad, good in SYNONYM_MAP.items():
        if bad in text:
            text = text.replace(bad, good)
    
    # 1. Extract Dish Name
    detected_dish = None
    # Sort dishes by length (desc) to match longest phrases first ("chicken biryani" vs "chicken")
    # Sort dishes by length (desc) to match longest phrases first ("chicken biryani" vs "chicken")
    sorted_dishes = sorted(KNOWN_DISHES, key=len, reverse=True)
    
    for dish in sorted_dishes:
        # Check exact string presence
        if dish in text:
            detected_dish = dish
            break
            
    # Fallback: Extraction for unknown dishes
    if not detected_dish:
        # Remove common stop phrases
        clean_text = text
        stop_phrases = [
            "i want to", "i would like to", "could you", "please", 
            "cook", "make", "prepare", "recipe", "for", 
            "members", "people", "persons", "servings", "serves"
        ]
        
        for phrase in stop_phrases:
            clean_text = clean_text.replace(phrase, " ")

        # Remove numbers
        clean_text = re.sub(r'\d+', ' ', clean_text)
        
        # Cleanup whitespace
        potential_dish = " ".join(clean_text.split())
        
        # Remove small joiners at start/end
        potential_dish = re.sub(r'^(a|an|the)\s+', '', potential_dish)
        
        if len(potential_dish) > 2: # heuristic min length
             detected_dish = potential_dish
            
    # 2. Extract Servings (People count)
    servings = 1
    
    # regex for "for X people" or just "X people" or standalone numbers
    # Strategy: Look for specific patterns first, then fallback
    
    # Matches: "for 2", "for 2 people", "serves 4"
    numeric_match = re.search(r'\b(for|serves)?\s*(\d+)\s*(people|persons|servings)?\b', text)
    if numeric_match:
         val = int(numeric_match.group(2))
         if val > 0:
             servings = val
    else:
        # Check text numbers
        for word, val in NUMBER_MAP.items():
            if f"for {word}" in text or f"{word} people" in text:
                servings = val
                break
                
    return {
        "dish": detected_dish,
        "servings": servings
    }
