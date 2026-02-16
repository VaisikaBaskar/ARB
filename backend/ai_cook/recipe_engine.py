# backend/ai_cook/recipe_engine.py
# Orchestrates AI modules to generate a full cooking response
# ISOLATED MODULE - PURE LOGIC

import json
import os
from .intent_parser import parse_intent
from .steps_generator import get_cooking_steps
from .response_formatter import format_ai_response
from .pantry_awareness import check_pantry_availability

BASE_RECIPES_PATH = os.path.join(os.path.dirname(__file__), 'base_recipes.json')

def generate_ai_response(raw_text, user_id=None):
    """
    Main orchestration function.
    1. Parse Intent
    2. Load Base Recipe
    3. Scale Ingredients
    4. Fetch Steps
    5. Check Pantry (if user_id)
    6. Format Response
    """
    
    # 1. Intent Extraction
    intent = parse_intent(raw_text)
    dish_name = intent.get("dish")
    target_servings = intent.get("servings", 1)
    
    if not dish_name:
        return {
            "success": False,
            "message": "I couldn't understand which dish you want to cook. I currently know: Chicken Biryani, Veg Pulao, Egg Fried Rice."
        }
        
    # 2. Load Base Recipe for Scaling
    # Try finding in Base Recipes first
    template = None
    if os.path.exists(BASE_RECIPES_PATH):
        try:
            with open(BASE_RECIPES_PATH, 'r') as f:
                base_recipes = json.load(f)
            template = next((r for r in base_recipes if r.get("dish") == dish_name), None)
        except Exception:
            pass # Continue to fallback if base load fails
            
    is_generated_dynamic = False
    
    # If not in base knowledge, use Dynamic Generation Rule
    if not template:
        # Dynamic Generator Logic
        # Heuristics based on dish name keywords
        
        # Default Template
        gen_ingredients = []
        gen_steps = []
        
        dish_lower = dish_name.lower()
        
        # Rule 1: Biryani / Rice
        if "biryani" in dish_lower or "pulao" in dish_lower or "rice" in dish_lower:
            main_item = "rice"
            protein = "mixed vegetables"
            if "chicken" in dish_lower: protein = "chicken"
            if "mutton" in dish_lower or "lamb" in dish_lower: protein = "mutton"
            if "egg" in dish_lower: protein = "hard boiled eggs"
            if "paneer" in dish_lower: protein = "paneer cubes"
            if "shrimp" in dish_lower or "prawn" in dish_lower: protein = "prawns"
            
            gen_ingredients = [
                {"name": "basmati rice", "quantity": 100, "unit": "g"},
                {"name": protein, "quantity": 150, "unit": "g" if "egg" not in protein else "count"},
                {"name": "onion", "quantity": 1, "unit": "medium"},
                {"name": "tomato", "quantity": 1, "unit": "medium"},
                {"name": "yogurt", "quantity": 50, "unit": "g"},
                {"name": "ginger garlic paste", "quantity": 1, "unit": "tbsp"},
                {"name": "biryani masala", "quantity": 1, "unit": "tbsp"},
                {"name": "turmeric powder", "quantity": 0.5, "unit": "tsp"},
                {"name": "red chilli powder", "quantity": 1, "unit": "tsp"},
                {"name": "green cardamom", "quantity": 2, "unit": "pods"},
                {"name": "cloves", "quantity": 2, "unit": "count"},
                {"name": "cinnamon stick", "quantity": 1, "unit": "inch"},
                {"name": "ghee", "quantity": 1, "unit": "tbsp"},
                {"name": "cooking oil", "quantity": 1, "unit": "tbsp"},
                {"name": "fresh coriander", "quantity": 1, "unit": "handful"},
                {"name": "mint leaves", "quantity": 10, "unit": "leaves"},
                {"name": "salt", "quantity": 1, "unit": "tsp (to taste)"}
            ]
            gen_steps = [
                f"Wash and soak basmati rice for 30 minutes.",
                f"Marinate {protein} with yogurt, ginger-garlic paste, turmeric, chilli powder, and salt.",
                "In a heavy pot, heat oil and ghee. Add whole spices (cardamom, cloves, cinnamon).",
                "Sauté sliced onions until golden brown and crispy.",
                f"Add marinated {protein} and cook on medium heat until tender.",
                "Boil water with salt and cook rice until 70% done. Drain.",
                "Layer the partially cooked rice over the meat/vegetable base.",
                "Sprinkle mint, coriander, and biryani masala on top.",
                "Cover tightly with a lid and cook on low heat (dum) for 15-20 minutes.",
                "Fluff gently and serve hot with raita."
            ]
            
        # Rule 2: Curry / Gravy
        elif "curry" in dish_lower or "masala" in dish_lower or "gravy" in dish_lower or "korma" in dish_lower:
            main_item = "mixed vegetables"
            if "chicken" in dish_lower: main_item = "chicken pieces"
            if "paneer" in dish_lower: main_item = "paneer cubes"
            if "egg" in dish_lower: main_item = "boiled eggs"
            if "fish" in dish_lower: main_item = "fish fillets"
            if "mutton" in dish_lower: main_item = "mutton pieces"
            
            gen_ingredients = [
                {"name": main_item, "quantity": 200, "unit": "g" if "egg" not in main_item else "count"},
                {"name": "onion", "quantity": 2, "unit": "medium"},
                {"name": "tomato", "quantity": 2, "unit": "medium"},
                {"name": "ginger garlic paste", "quantity": 1, "unit": "tbsp"},
                {"name": "turmeric powder", "quantity": 0.5, "unit": "tsp"},
                {"name": "coriander powder", "quantity": 1, "unit": "tsp"},
                {"name": "cumin powder", "quantity": 0.5, "unit": "tsp"},
                {"name": "garam masala", "quantity": 0.5, "unit": "tsp"},
                {"name": "red chilli powder", "quantity": 1, "unit": "tsp"},
                {"name": "cooking oil", "quantity": 2, "unit": "tbsp"},
                {"name": "salt", "quantity": 1, "unit": "tsp"},
                {"name": "fresh coriander", "quantity": 1, "unit": "tbsp"}
            ]
            gen_steps = [
                f"Heat oil in a pan.",
                "Add chopped onions and sauté until translucent.",
                "Add ginger-garlic paste and cook for a minute until raw smell goes.",
                "Add chopped tomatoes, turmeric, coriander powder, cumin powder, and chilli powder.",
                "Cook until oil separates from the masala.",
                f"Add {main_item} and mix well to coat with spices.",
                "Add water to adjust consistency, cover and simmer until cooked through.",
                "Sprinkle garam masala and garnish with fresh coriander.",
                "Serve hot with rice or roti."
            ]
            
        # Rule 3: Noodles / Pasta
        elif "noodles" in dish_lower or "pasta" in dish_lower or "chowmein" in dish_lower:
             base_carb = "noodles" if "noodles" in dish_lower or "chowmein" in dish_lower else "penne pasta"
             gen_ingredients = [
                 {"name": base_carb, "quantity": 150, "unit": "g"},
                 {"name": "carrot", "quantity": 1, "unit": "medium"},
                 {"name": "capsicum", "quantity": 0.5, "unit": "medium"},
                 {"name": "cabbage", "quantity": 50, "unit": "g"},
                 {"name": "garlic", "quantity": 3, "unit": "cloves"},
                 {"name": "soy sauce", "quantity": 1, "unit": "tbsp"},
                 {"name": "vinegar", "quantity": 1, "unit": "tsp"},
                 {"name": "chilli sauce", "quantity": 1, "unit": "tsp"},
                 {"name": "cooking oil", "quantity": 2, "unit": "tbsp"},
                 {"name": "salt", "quantity": 0.5, "unit": "tsp"},
                 {"name": "black pepper", "quantity": 0.5, "unit": "tsp"}
             ]
             gen_steps = [
                 f"Boil {base_carb} in salted water until al dente/cooked. Drain and toss with a little oil.",
                 "Heat oil in a wok or large pan on high heat.",
                 "Add minced garlic and sauté for 30 seconds.",
                 "Add sliced carrots, cabbage, and capsicum. Stir-fry for 2 minutes (keep them crunchy).",
                 f"Add the boiled {base_carb}.",
                 "Add soy sauce, vinegar, chilli sauce, salt, and pepper.",
                 "Toss everything well on high heat for 2 minutes.",
                 "Serve hot immediately."
             ]
             
        # Fallback General
        else:
             gen_ingredients = [
                 {"name": "main ingredient (meat/veg)", "quantity": 250, "unit": "g"},
                 {"name": "onion", "quantity": 1, "unit": "medium"},
                 {"name": "tomato", "quantity": 1, "unit": "medium"},
                 {"name": "cooking oil", "quantity": 1, "unit": "tbsp"},
                 {"name": "ginger garlic paste", "quantity": 1, "unit": "tsp"},
                 {"name": "turmeric powder", "quantity": 0.25, "unit": "tsp"},
                 {"name": "red chilli powder", "quantity": 0.5, "unit": "tsp"},
                 {"name": "salt", "quantity": 1, "unit": "tsp"}
             ]
             gen_steps = [
                 "Prep all ingredients by chopping and washing.",
                 "Heat oil in a pan over medium heat.",
                 "Sauté onions until they turn soft.",
                 "Add ginger-garlic paste and tomatoes, cooking until soft.",
                 "Add the main ingredient and powdered spices.",
                 "Cook covered until the main ingredient is tender.",
                 "Adjust salt and serve warm."
             ]

        template = {
            "dish": dish_name,
            "base_servings": 1,
            "ingredients": gen_ingredients,
            "steps": gen_steps
        }
        is_generated_dynamic = True

    base_servings = template.get("base_servings", 1)
    base_ingredients = template.get("ingredients", [])
    
    # 3. Simple Quantity Scaling (Linear)
    # Ratio = Target / Base
    scale_ratio = target_servings / base_servings
    
    scaled_ingredients = []
    required_ingredients_for_pantry = [] # For pantry check
    
    for ing in base_ingredients:
        name = ing.get("name")
        qty = ing.get("quantity", 0)
        unit = ing.get("unit")
        
        # Scale
        new_qty = qty * scale_ratio
        
        # Rounding for cleanliness (e.g. 1.0 instead of 1.0000001)
        if new_qty % 1 == 0:
            new_qty = int(new_qty)
        else:
            new_qty = round(new_qty, 2)
            
        scaled_ingredients.append({
            "name": name,
            "quantity": new_qty,
            "unit": unit
        })
        
        required_ingredients_for_pantry.append({"name": name})

    # 4. Fetch Cooking Steps
    if is_generated_dynamic:
        steps = template.get("steps", [])
    else:
        steps_data = get_cooking_steps({"dish": dish_name})
        if "error" in steps_data:
            return {"success": False, "message": steps_data["error"]}
            
        steps = steps_data.get("steps", [])
    
    # 5. Pantry Awareness (Optional)
    pantry_status = {
        "available": [],
        "missing": []
    }
    
    if user_id:
        pantry_status = check_pantry_availability({
            "user_id": user_id,
            "ingredients": required_ingredients_for_pantry
        })

    # 6. Final Formatting
    formatted_output = format_ai_response({
        "dish": dish_name,
        "servings": target_servings,
        "ingredients": scaled_ingredients,
        "steps": steps
    })
    
    # Construct Final API Response
    return {
        "success": True,
        "data": {
            "title": formatted_output["title"],
            "ingredients": formatted_output["ingredients"],
            "steps": formatted_output["steps"],
            "pantry": pantry_status,
            "is_generated": is_generated_dynamic,
            "generated_recipe": {
                "name": dish_name.title(),
                "ingredients": scaled_ingredients,
                "cooking_steps": steps,
                "cuisine": "Unknown" if is_generated_dynamic else "General",
                "dietary_tags": []  
            } if is_generated_dynamic else None
        }
    }
