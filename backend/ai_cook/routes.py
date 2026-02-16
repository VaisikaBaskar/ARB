from flask import Blueprint, jsonify, request, session
from datetime import datetime
import uuid
import sys
import os

# Ensure access to sibling/parent modules for DB access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from db import db
except ImportError:
    from backend.db import db

from .recipe_engine import generate_ai_response

# Define Blueprint but DO NOT register it in the main app yet
# This ensures total isolation until explicitly enabled.
ai_cook_bp = Blueprint('ai_cook', __name__, url_prefix='/ai')

@ai_cook_bp.route('/status', methods=['GET'])
def check_status():
    return jsonify({
        "status": "online",
        "module": "AI Cooking Assistant",
        "message": "Ready for instructions."
    })

@ai_cook_bp.route('/cook', methods=['POST'])
def generate_cooking_response():
    try:
        data = request.json
        text = data.get("text", "")
        # UX Correction: Derive user_id from session preferably, or from body
        user_id = session.get("user_id") or data.get("user_id") # Consistent with main app
        
        if not text:
             return jsonify({
                 "success": False, 
                 "message": "Please describe what you want to cook."
             }), 400
             
        response = generate_ai_response(text, user_id)
        
        # --- Auto-Save Logic for Dynamically Generated Recipes ---
        # If the recipe was dynamically generated (unknown dish), save it to DB
        # so it becomes "known" for future requests.
        try:
            if response.get("success") and response["data"].get("is_generated"):
                 generated_recipe = response["data"].get("generated_recipe")
                 if generated_recipe:
                     # Create Slug ID
                     slug = generated_recipe["name"].lower().replace(" ", "_")
                     ai_id = f"ai_auto_{slug}"[:50] # Limit length
                     
                     generated_recipe["recipe_id"] = ai_id
                     generated_recipe["source"] = "ai_assistant"
                     generated_recipe["generated"] = True
                     
                     # Upsert
                     db.recipes.update_one(
                        {"recipe_id": ai_id},
                        {"$set": generated_recipe},
                        upsert=True
                     )
                     print(f"Auto-saved new AI recipe: {ai_id}")
        except Exception as save_err:
             print(f"Auto-save warning: {save_err}") # Non-blocking

        return jsonify(response)
        
    except Exception as e:
        print(f"AI Engine Error: {e}")
        return jsonify({
            "success": False,
            "message": "I encountered an error while thinking. Please try again."
        }), 500

@ai_cook_bp.route('/save-recipe', methods=['POST'])
def save_ai_recipe():
    try:
        data = request.json
        recipe_data = data.get("recipe", {})
        
        if not recipe_data:
            return jsonify({"success": False, "message": "No recipe data provided"}), 400

        # Generate ID if missing (AI recipes usually don't have one allocated until save)
        if not recipe_data.get("recipe_id"):
            # Create a unique AI ID
            recipe_data["recipe_id"] = f"ai_{uuid.uuid4().hex[:8]}"

        # Enforce AI Source flag
        recipe_data["source"] = "ai"
        recipe_data["is_virtual"] = False # Now it's real
        
        # Upsert into Recipes Collection
        db.recipes.update_one(
            {"recipe_id": recipe_data["recipe_id"]},
            {"$set": recipe_data},
            upsert=True
        )
        
        return jsonify({
            "success": True, 
            "message": "Saved to My Recipes",
            "recipe_id": recipe_data["recipe_id"]
        })

    except Exception as e:
        print(f"AI Save Error: {e}")
        return jsonify({
            "success": False,
            "message": "Failed to save recipe."
        }), 500

