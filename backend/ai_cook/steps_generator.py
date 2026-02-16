# backend/ai_cook/steps_generator.py
# Retrieves cooking steps from the Base Recipe Store
# ISOLATED MODULE - READ ONLY

import json
import os

BASE_RECIPES_PATH = os.path.join(os.path.dirname(__file__), 'base_recipes.json')

def get_cooking_steps(input_data):
    """
    Retrieves static cooking steps for a given dish.
    Input: { "dish": "string" }
    Output: { "dish": "string", "steps": ["..."] } or { "error": "..." }
    """
    requested_dish = input_data.get("dish")
    
    if not requested_dish:
        return {"error": "No dish specified"}

    # Load Base Recipes
    if not os.path.exists(BASE_RECIPES_PATH):
        return {"error": "Base recipe store not found"}

    try:
        with open(BASE_RECIPES_PATH, 'r') as f:
            base_recipes = json.load(f)
    except Exception as e:
        return {"error": f"Failed to load recipe store: {str(e)}"}

    # Find the dish (case-insensitive)
    requested_dish_lower = requested_dish.lower().strip()
    
    found_recipe = None
    for recipe in base_recipes:
        if recipe.get("dish", "").lower() == requested_dish_lower:
            found_recipe = recipe
            break
            
    if not found_recipe:
         return {"error": "Base recipe not available for this dish"}

    # Extract Steps
    steps = found_recipe.get("steps", [])
    
    return {
        "dish": found_recipe.get("dish"), # Return canonical name
        "steps": steps
    }
