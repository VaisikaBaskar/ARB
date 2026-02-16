# backend/ai_cook/pantry_awareness.py
# Checks ingredient availability in user's pantry
# ISOLATED MODULE - READ ONLY

import sys
import os

# Ensure access to sibling/parent modules for DB access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from db import db
except ImportError:
    # Fallback to absolute import if running from root
    from backend.db import db

def check_pantry_availability(input_data):
    """
    Checks which required ingredients are in the user's pantry.
    Input: {
      "user_id": "string | null",
      "ingredients": [ { "name": "...", ... }, ... ]
    }
    Output: {
      "available": ["ingredient name", ...],
      "missing": ["ingredient name", ...]
    }
    """
    user_id = input_data.get("user_id")
    ingredients = input_data.get("ingredients", [])
    
    # 1. Graceful Exit if no user or ingredients
    if not user_id or not ingredients:
        return {
            "available": [],
            "missing": [ing.get("name") for ing in ingredients if ing.get("name")]
        }

    # 2. Fetch Pantry Items (Read-Only)
    try:
        pantry_items = list(db.pantry.find({"user_id": user_id}, {"_id": 0, "ingredient": 1}))
        pantry_set = {item.get("ingredient", "").lower().strip() for item in pantry_items}
    except Exception as e:
        # Graceful failure: assume nothing is available
        print(f"Pantry Check Error: {e}")
        return {
            "available": [],
            "missing": [ing.get("name") for ing in ingredients if ing.get("name")]
        }

    # 3. Compare Ingredients
    available = []
    missing = []

    for ing in ingredients:
        name = ing.get("name", "")
        if not name:
            continue
            
        name_lower = name.lower().strip()
        
        # Exact Name Match (Case-Insensitive) as per requirements
        if name_lower in pantry_set:
            available.append(name)
        else:
            missing.append(name)
            
    return {
        "available": available,
        "missing": missing
    }
