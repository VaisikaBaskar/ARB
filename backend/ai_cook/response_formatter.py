# backend/ai_cook/response_formatter.py
# Formats final AI response for the frontend
# ISOLATED MODULE - PURE LOGIC

def format_ai_response(data):
    """
    Formats the cooking plan into a user-friendly structure.
    Input: {
      "dish": "string",
      "servings": int,
      "ingredients": [ { "name": "...", "quantity": ..., "unit": "..." }, ... ],
      "steps": ["...", ...]
    }
    Output: { "title": "...", "ingredients": ["..."], "steps": ["..."] }
    """
    dish = data.get("dish", "Unknown Dish")
    servings = data.get("servings", 1)
    ingredients_raw = data.get("ingredients", [])
    steps_raw = data.get("steps", [])

    # 1. Format Title
    title = f"{dish.title()} – For {servings} People"
    if servings == 1:
        title = f"{dish.title()} – For 1 Person"

    # 2. Format Ingredients List
    formatted_ingredients = []
    for ing in ingredients_raw:
        name = ing.get("name", "").title()
        qty = ing.get("quantity", 0)
        unit = ing.get("unit", "")
        
        # Format: "Basmati Rice: 200 g"
        # Handle count units gracefully (e.g. "Onion: 1 count" -> "Onion: 1")
        if unit == "count":
            line = f"{name}: {qty}"
        else:
             line = f"{name}: {qty} {unit}"
        
        formatted_ingredients.append(line)

    # 3. Format Steps (Numbering)
    formatted_steps = []
    for i, step in enumerate(steps_raw, 1):
        formatted_steps.append(f"{i}. {step}")

    return {
        "title": title,
        "ingredients": formatted_ingredients,
        "steps": formatted_steps
    }
