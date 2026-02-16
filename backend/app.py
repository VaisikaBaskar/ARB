from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from db import db
from collections import Counter
import json
import urllib.request
import urllib.error
import os
from bson import ObjectId

app = Flask(__name__, static_folder="../frontend", static_url_path="/")
app.secret_key = "super_secret_ai_recipe_box_key" 
# Ensure session cookies work on localhost (HTTP)
app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False
)
CORS(app, supports_credentials=True)

# --- CHECKPOINT 32: AI Cooking Assistant Module ---
# Isolated registration of the AI blueprint
# This enables the /ai/cook and /ai/status endpoints
try:
    from ai_cook.routes import ai_cook_bp
    app.register_blueprint(ai_cook_bp)
except ImportError as e:
    print(f"Warning: AI Cooking Assistant module not loaded. Reason: {e}")
except Exception as e:
    print(f"Error registering AI blueprint: {e}")

# --- CHECKPOINT 14: Ingredient Synonyms Map ---
# Static map for similarity matching (Additive logic)
INGREDIENT_SYNONYMS = {
    "onion": ["shallot", "spring onion", "scallion", "red onion"],
    "rice": ["brown rice", "basmati", "white rice", "jasmine rice", "arborio rice"],
    "milk": ["soy milk", "almond milk", "oat milk", "cow milk", "coconut milk"],
    "chicken": ["chicken breast", "chicken thigh", "roast chicken", "grilled chicken"],
    "sugar": ["brown sugar", "white sugar", "honey", "maple syrup"],
    "flour": ["all-purpose flour", "whole wheat flour", "bread flour"],
    "oil": ["olive oil", "vegetable oil", "canola oil", "coconut oil"]
}

# --- CHECKPOINT 15: External Discovery Layer ---

SEASONAL_INGREDIENTS_MAP = {
    "summer": ["cucumber", "watermelon", "curd", "mango", "corn", "tomato"],
    "winter": ["carrot", "spinach", "peas", "radish", "sweet potato"],
    "monsoon": ["corn", "ginger", "turmeric"]
}

EXTERNAL_RECIPES_FALLBACK = [
    {
        "external_id": "ext_001",
        "name": "Classic Margherita Pizza",
        "ingredients": ["flow", "tomato", "cheese", "basil", "oil"],
        "cuisine": "Italian",
        "source": "external_mock"
    },
    {
        "external_id": "ext_002",
        "name": "Mango Smoothie",
        "ingredients": ["mango", "yogurt", "honey", "milk"],
        "cuisine": "Global",
        "source": "external_mock"
    },
    {
        "external_id": "ext_003",
        "name": "Winter Vegetable Soup",
        "ingredients": ["carrot", "spinach", "peas", "onion", "garlic"],
        "cuisine": "Global",
        "source": "external_mock"
    }
]

def get_current_season():
    month = datetime.utcnow().month
    if 3 <= month <= 6:
        return "summer"
    elif 7 <= month <= 9:
        return "monsoon"
    elif 10 <= month <= 12 or 1 <= month <= 2:
        return "winter"
    return "summer"

def fetch_external_recipes():
    # Attempt to fetch from TheMealDB (Free API, no key required)
    url = "https://www.themealdb.com/api/json/v1/1/search.php?s=chicken" 
    
    recipes = []
    try:
        # Timeout configured for fail-safe behavior
        with urllib.request.urlopen(url, timeout=2) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode())
                meals = data.get("meals") or []
                
                # Normalize up to 5 meals
                for meal in meals[:5]:
                    ings = []
                    # TheMealDB has ingredients in strIngredient1..20
                    for i in range(1, 21):
                        ing = meal.get(f"strIngredient{i}")
                        if ing and ing.strip():
                            ings.append(ing.strip())
                    
                    recipes.append({
                        "external_id": meal.get("idMeal"),
                        "name": meal.get("strMeal"),
                        "ingredients": ings,
                        "cuisine": meal.get("strArea"),
                        "source": "external_api"
                    })
    except Exception:
        # Silently fail and use fallback
        pass

    if not recipes:
        return EXTERNAL_RECIPES_FALLBACK
        
    return recipes

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/<path:path>")
def serve_static(path):
    return app.send_static_file(path)

# --- CHECKPOINT 29: Authentication Layer ---
@app.route("/auth/signup", methods=["POST"])
def auth_signup():
    data = request.json
    raw_user_id = data.get("user_id", "")
    password = data.get("password", "")

    if not raw_user_id or not password:
        return jsonify({"error": "User ID and Password are required"}), 400
    
    # Authentication Input Normalization - Bug Fix
    # Normalize user_id to lowercase and strip whitespace to prevent duplicates/mismatches
    user_id = raw_user_id.strip().lower()
    clean_password = password.strip()

    # Check if user exists
    existing_user = db.auth_users.find_one({"user_id": user_id})
    if existing_user:
        return jsonify({"error": "User ID already exists"}), 409

    hashed_pw = generate_password_hash(clean_password)
    
    # Create new auth user
    db.auth_users.insert_one({
        "user_id": user_id,
        "password_hash": hashed_pw,
        "created_at": datetime.utcnow()
    })
    
    return jsonify({"message": "Account created successfully"}), 201

@app.route("/auth/login", methods=["POST"])
def auth_login():
    data = request.json
    raw_user_id = data.get("user_id", "")
    password = data.get("password", "")
    
    print(f"\n--- DEBUG LOGIN START ---")
    print(f"DEBUG: Raw user_id: '{raw_user_id}', repr: {repr(raw_user_id)}")
    
    if not raw_user_id or not password:
        return jsonify({"error": "User ID and Password are required"}), 400

    # Authentication Input Normalization - Bug Fix
    normalized_user_id = raw_user_id.strip().lower()
    clean_password = password.strip()
    
    print(f"DEBUG: Normalized user_id: '{normalized_user_id}'")
    print(f"DEBUG: Password length: {len(clean_password)}")

    # Attempt 1: Lookup with normalized (standard) user_id
    user = db.auth_users.find_one({"user_id": normalized_user_id})
    print(f"DEBUG: Lookup 1 (Norm) Found: {bool(user)}")
    
    # Attempt 2: Backward Compatibility - Lookup with raw user_id (for legacy users)
    if not user:
        print(f"DEBUG: Lookup 1 failed. Trying Raw: '{raw_user_id}'")
        user = db.auth_users.find_one({"user_id": raw_user_id})
        print(f"DEBUG: Lookup 2 (Raw) Found: {bool(user)}")
    
    if user:
        print(f"DEBUG: User Found. ID: {user.get('user_id')}")
        print(f"DEBUG: Stored Hash (first 20): {user.get('password_hash', '')[:20]}...")
        
        is_valid = check_password_hash(user["password_hash"], clean_password)
        print(f"DEBUG: Password Check Result: {is_valid}")
        
        if is_valid:
            # Use the stored user_id for the session to maintain consistency
            session["user_id"] = user["user_id"]
            session.permanent = True
            print(f"DEBUG: Session populated: {session}")
            print(f"--- DEBUG LOGIN END (SUCCESS) ---\n")
            return jsonify({"message": "Login successful", "user_id": user["user_id"]}), 200
    else:
        print(f"DEBUG: User Not Found in DB (Total users: {db.auth_users.count_documents({})})")

    print(f"--- DEBUG LOGIN END (FAILURE) ---\n")
    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/auth/logout", methods=["POST"])
def auth_logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200

@app.route("/auth/me", methods=["GET"])
def auth_check():
    user_id = session.get("user_id")
    if user_id:
        return jsonify({"user_id": user_id}), 200
    return jsonify({"user_id": None}), 200

@app.route("/user", methods=["POST"])
def create_or_update_user():
    data = request.json
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    # Upsert user document
    db.users.update_one(
        {"user_id": user_id},
        {"$set": data},
        upsert=True
    )

    return jsonify({"message": "User profile saved"}), 200

@app.route("/user/<user_id>", methods=["GET"])
def get_user(user_id):
    user = db.users.find_one({"user_id": user_id}, {"_id": 0})
    
    if user:
        return jsonify(user), 200
    else:
        return jsonify({"message": "User not found"}), 404

@app.route("/user/profile", methods=["POST"])
def update_user_profile():
    data = request.json
    # UX Correction: Derive user_id from session first
    user_id = session.get("user_id") or data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    profile_data = {
        "diet": data.get("diet"),
        "dietary_tags": data.get("dietary_tags", []),
        "favorite_cuisines": data.get("favorite_cuisines", []),
        "liked_ingredients": data.get("liked_ingredients", []),
        "disliked_ingredients": data.get("disliked_ingredients", [])
    }

    db.users.update_one(
        {"user_id": user_id},
        {"$set": profile_data},
        upsert=True
    )
    
    return jsonify({"message": "User preferences updated"}), 200

@app.route("/user/profile/<user_id>", methods=["GET"])
def get_user_profile(user_id):
    # UX Correction: Derive user_id from session first
    user_id = session.get("user_id") or user_id
    user = db.users.find_one({"user_id": user_id}, {"_id": 0})
    
    if user:
        return jsonify({
            "user_id": user_id,
            "diet": user.get("diet"),
            "dietary_tags": user.get("dietary_tags", []),
            "favorite_cuisines": user.get("favorite_cuisines", []),
            "liked_ingredients": user.get("liked_ingredients", []),
            "disliked_ingredients": user.get("disliked_ingredients", [])
        }), 200
    else:
        return jsonify({
            "user_id": user_id,
            "diet": None, 
            "dietary_tags": [],
            "favorite_cuisines": [],
            "liked_ingredients": [],
            "disliked_ingredients": []
        }), 200

@app.route("/recipe", methods=["POST"])
def create_or_update_recipe():
    data = request.json
    recipe_id = data.get("recipe_id")

    if not recipe_id:
        return jsonify({"error": "recipe_id is required"}), 400

    raw_ingredients = data.get("ingredients", [])
    normalized_ingredients = []

    for item in raw_ingredients:
        if isinstance(item, str):
            normalized_ingredients.append({"name": item, "quantity": ""})
        elif isinstance(item, dict):
            normalized_ingredients.append(item)
    
    data["ingredients"] = normalized_ingredients
    
    if "cooking_steps" not in data:
        data["cooking_steps"] = []
    if "dietary_tags" not in data:
        data["dietary_tags"] = []

    db.recipes.update_one(
        {"recipe_id": recipe_id},
        {"$set": data},
        upsert=True
    )

    return jsonify({"message": "Recipe saved successfully"}), 200

@app.route("/recipe/<recipe_id>", methods=["DELETE"])
def delete_recipe(recipe_id):
    result = db.recipes.delete_one({"recipe_id": recipe_id})
    
    if result.deleted_count > 0:
        return jsonify({"message": "Recipe deleted successfully"}), 200
    else:
        return jsonify({"message": "Recipe not found"}), 404

@app.route("/recipes", methods=["GET"])
def get_recipes():
    recipes = list(db.recipes.find({}, {"_id": 0}))
    return jsonify(recipes), 200

@app.route("/recipe/<recipe_id>", methods=["GET"])
def get_recipe(recipe_id):
    recipe = db.recipes.find_one({"recipe_id": recipe_id}, {"_id": 0})

    if recipe:
        return jsonify(recipe), 200
    else:
        return jsonify({"message": "Recipe not found"}), 404

@app.route("/pantry", methods=["POST"])
def create_or_update_pantry_item():
    data = request.json
    # UX Correction: Derive user_id from session first
    user_id = session.get("user_id") or data.get("user_id")
    ingredient = data.get("ingredient")

    if not user_id or not ingredient:
        return jsonify({"error": "user_id and ingredient are required"}), 400

    db.pantry.update_one(
        {"user_id": user_id, "ingredient": ingredient},
        {"$set": data},
        upsert=True
    )

    return jsonify({"message": "Pantry item saved successfully"}), 200

@app.route("/pantry/<user_id>", methods=["GET"])
def get_pantry_items(user_id):
    # UX Correction: Derive user_id from session first (overrides URL param if logged in)
    user_id = session.get("user_id") or user_id
    items = list(db.pantry.find({"user_id": user_id}, {"_id": 0}))
    current_date = datetime.utcnow().strftime('%Y-%m-%d')
    pantry_list = []
    
    for item in items:
        expiry = item.get("expiry_date")
        is_expired = False
        if expiry and expiry < current_date:
            is_expired = True
        item["is_expired"] = is_expired
        pantry_list.append(item)

    return jsonify(pantry_list), 200

@app.route("/pantry/<user_id>/<ingredient>", methods=["DELETE"])
def delete_pantry_item(user_id, ingredient):
    result = db.pantry.delete_one({"user_id": user_id, "ingredient": ingredient})

    if result.deleted_count > 0:
        return jsonify({"message": "Pantry item removed successfully"}), 200
    else:
        return jsonify({"message": "Item not found"}), 404

@app.route("/missing-ingredients/<user_id>/<recipe_id>", methods=["GET"])
def get_missing_ingredients(user_id, recipe_id):
    # UX Correction: Derive user_id from session first
    user_id = session.get("user_id") or user_id
    recipe = db.recipes.find_one({"recipe_id": recipe_id})
    if not recipe:
        return jsonify({"error": "Recipe not found"}), 404
        
    recipe_ingredients = set()
    raw_ingredients = recipe.get("ingredients", [])
    
    for ing in raw_ingredients:
        if isinstance(ing, dict):
             name = ing.get("name")
             if name: 
                 recipe_ingredients.add(name.lower())
        else:
             recipe_ingredients.add(str(ing).lower())

    pantry_items = list(db.pantry.find({"user_id": user_id}, {"ingredient": 1}))
    pantry_ingredients = {item["ingredient"].lower() for item in pantry_items}
    
    missing = list(recipe_ingredients - pantry_ingredients)
    
    return jsonify({
        "recipe_id": recipe_id,
        "missing_ingredients": missing
    }), 200

@app.route("/shopping-list/<user_id>", methods=["POST"])
def generate_shopping_list(user_id):
    # UX Correction: Derive user_id from session first
    user_id = session.get("user_id") or user_id
    data = request.json
    recipe_ids = data.get("recipe_ids", [])
    
    if not recipe_ids:
         return jsonify({"shopping_list": []}), 200

    pantry_items = list(db.pantry.find({"user_id": user_id}, {"_id": 0}))
    current_date = datetime.utcnow().strftime('%Y-%m-%d')
    warning_threshold = (datetime.utcnow() + timedelta(days=2)).strftime('%Y-%m-%d')
    
    pantry_map = {}
    for item in pantry_items:
        ing_lower = item["ingredient"].lower()
        expiry = item.get("expiry_date")
        is_expired = False
        if expiry and expiry < current_date:
            is_expired = True
        
        pantry_map[ing_lower] = {
            "is_expired": is_expired,
            "expiry_date": expiry
        }

    needed_ingredients = set()
    
    for rid in recipe_ids:
        recipe = db.recipes.find_one({"recipe_id": rid})
        if not recipe:
            continue
            
        raw_ingredients = recipe.get("ingredients", [])
        for ing in raw_ingredients:
            if isinstance(ing, dict):
                name = ing.get("name")
                if name: 
                    needed_ingredients.add(name.lower())
            else:
                needed_ingredients.add(str(ing).lower())

    shopping_list = []
    
    for ing in needed_ingredients:
        pantry_info = pantry_map.get(ing)
        
        if not pantry_info:
            shopping_list.append({
                "ingredient": ing,
                "action": "buy"
            })
            continue
            
        if pantry_info["is_expired"]:
            shopping_list.append({
                "ingredient": ing,
                "action": "replace"
            })
        else:
            expiry_date = pantry_info.get("expiry_date")
            if expiry_date and expiry_date <= warning_threshold:
                 shopping_list.append({
                     "ingredient": ing,
                     "action": "available",
                     "warning": "expiring_soon"
                 })

    return jsonify({"shopping_list": shopping_list}), 200



# Validates imports are present
import json
import os

# ... [Keep existing imports]

# --- Config: Legacy Names ---
LEGACY_NAMES_PATH = os.path.join(os.path.dirname(__file__), "config", "legacy_recipe_names.json")
LEGACY_NAMES = {}
try:
    if os.path.exists(LEGACY_NAMES_PATH):
        with open(LEGACY_NAMES_PATH, "r") as f:
            LEGACY_NAMES = json.load(f)
            print(f"Loaded {len(LEGACY_NAMES)} legacy recipe names.")
except Exception as e:
    print(f"Warning: Failed to load legacy names: {e}")


@app.route("/meal-history/<user_id>", methods=["GET"])
def get_meal_history(user_id):
    # UX Correction: Derive user_id from session first
    user_id = session.get("user_id") or user_id
    
    # 1. Fetch History
    history = list(db.meal_history.find({"user_id": user_id}, {"_id": 0}).sort("cooked_at", -1))
    
    # 2. Identify missing names & collect IDs for batching
    missing_indices = []
    string_ids_to_query = set()
    object_ids_to_query_map = {} # str(oid) -> oid object
    
    for idx, item in enumerate(history):
        r_name = item.get("recipe_name")
        # Check if name is truly missing (None, empty, or whitespace)
        if not r_name or not str(r_name).strip():
            # Optimization: Check legacy map EARLY to avoid DB query if possible?
            # User requirement: "Keep batched live join". We can check legacy *after* query or *before*. 
            # But the requirement says "Resolution priority: 1) history... 2) DB... 3) Legacy."
            # So collecting IDs for DB lookup is correct first.
            missing_indices.append(idx)
            r_id = item.get("recipe_id")
            
            if r_id:
                # Add to string lookup set
                string_ids_to_query.add(str(r_id))
                
                # Check if valid ObjectId for secondary lookup
                if ObjectId.is_valid(r_id):
                    try:
                        oid = ObjectId(r_id)
                        object_ids_to_query_map[str(oid)] = oid
                    except:
                        pass

    # 3. Batch Queries (Max 2)
    map_by_recipe_id = {}
    map_by_object_id = {}
    
    # Query A: String match (recipe_id)
    if string_ids_to_query:
        cursor_a = db.recipes.find(
            {"recipe_id": {"$in": list(string_ids_to_query)}},
            {"recipe_id": 1, "name": 1, "recipe_name": 1}
        )
        for r in cursor_a:
            name = r.get("name") or r.get("recipe_name")
            if name:
                map_by_recipe_id[str(r.get("recipe_id"))] = name

    # Query B: ObjectId match (_id)
    if object_ids_to_query_map:
        cursor_b = db.recipes.find(
            {"_id": {"$in": list(object_ids_to_query_map.values())}},
            {"name": 1, "recipe_name": 1}
        )
        for r in cursor_b:
            name = r.get("name") or r.get("recipe_name")
            if name:
                map_by_object_id[str(r.get("_id"))] = name

    # 4. Resolve Names
    resolve_count_rid = 0
    resolve_count_oid = 0
    resolve_count_legacy = 0
    fallback_count = 0
    
    for idx in missing_indices:
        item = history[idx]
        r_id = str(item.get("recipe_id", ""))
        resolved_name = None
        
        # Priority 1: recipe_id map (DB)
        if r_id in map_by_recipe_id:
            resolved_name = map_by_recipe_id[r_id]
            resolve_count_rid += 1
        # Priority 2: ObjectId map (DB)
        elif r_id in map_by_object_id:
            resolved_name = map_by_object_id[r_id]
            resolve_count_oid += 1
        # Priority 3: Legacy Map (Config)
        elif r_id in LEGACY_NAMES:
            resolved_name = LEGACY_NAMES[r_id]
            resolve_count_legacy += 1
        # Priority 4: Fallback
        else:
             resolved_name = "Unknown Dish"
             fallback_count += 1
            
        # Apply strict write rule: Only to response dict, no DB write
        item["recipe_name"] = resolved_name
        item["display_name"] = resolved_name

    # 5. Ensure consistency for items that HAD names
    for item in history:
        if "display_name" not in item:
             item["display_name"] = item.get("recipe_name") or "Unknown Dish"

    # Logging (Minimal)
    if len(missing_indices) > 0:
        print(f"DEBUG: History Live Join Stats | Total: {len(history)} | Missing: {len(missing_indices)} | DB(RID): {resolve_count_rid} | DB(OID): {resolve_count_oid} | Legacy: {resolve_count_legacy} | Fallback: {fallback_count}")

    return jsonify(history), 200

@app.route("/meal-history", methods=["POST"])
def record_meal_history():
    data = request.json
    # UX Correction: Derive user_id from session first
    user_id = session.get("user_id") or data.get("user_id")
    recipe_id = data.get("recipe_id")
    # Checkpoint 19: Optional field to track source
    cooked_from_rec = data.get("cooked_from_recommendation", False)

    if not user_id or not recipe_id:
        return jsonify({"error": "user_id and recipe_id are required"}), 400

    # Lookup recipe name (Strategy A & B)
    recipe_name = "Unknown Recipe"
    recipe_cuisine = "Unknown"
    
    found_recipe = None
    
    # Strategy A: recipe_id field string match
    found_recipe = db.recipes.find_one({"recipe_id": recipe_id})
    
    # Strategy B: ObjectId match (fallback)
    if not found_recipe:
        try:
            found_recipe = db.recipes.find_one({"_id": ObjectId(recipe_id)})
        except Exception:
            pass # Invalid ObjectId
            
    if found_recipe:
        recipe_name = found_recipe.get("name") or found_recipe.get("recipe_name") or "Unknown Recipe"
        recipe_cuisine = found_recipe.get("cuisine") or "Unknown"

    # Insert meal history with cached name/cuisine (Additive)
    meal_record = {
        "user_id": user_id,
        "recipe_id": recipe_id,
        "recipe_name": recipe_name,
        "recipe_cuisine": recipe_cuisine,
        "cooked_at": datetime.utcnow()
    }
    # Add optional field if provided (Checkpoint 19)
    if cooked_from_rec:
        meal_record["cooked_from_recommendation"] = True
        
    db.meal_history.insert_one(meal_record)

    # Update user_behavior_stats
    recipe = found_recipe # Use the one we found
    if recipe:
        update_op_stats = {
            "$set": {"last_updated": datetime.utcnow()},
            "$inc": {}
        }
        
        # Track Cuisine Frequency
        if recipe.get("cuisine"):
             cuisine_key = f"cuisine_frequency.{recipe['cuisine']}"
             update_op_stats["$inc"][cuisine_key] = 1

        # Track Ingredient Frequency
        raw_ingredients = recipe.get("ingredients", [])
        
        # Checkpoint 19: Update Pantry 'last_used_at'
        # We need to identify which ingredients from the recipe are in the pantry
        recipe_ing_names = set()

        for ing in raw_ingredients:
            ing_name = ing.get("name") if isinstance(ing, dict) else str(ing)
            if ing_name:
                # Update Stats
                safe_key = ing_name.replace(".", "_") 
                update_op_stats["$inc"][f"ingredient_frequency.{safe_key}"] = 1
                
                # Collect for Pantry Update
                recipe_ing_names.add(ing_name.lower())
        
        if update_op_stats["$inc"]:
            db.user_behavior_stats.update_one(
                {"user_id": user_id},
                update_op_stats,
                upsert=True
            )
            
        # Checkpoint 19: Batch Update Pantry Usage
        if recipe_ing_names:
            db.pantry.update_many(
                {
                    "user_id": user_id,
                    "ingredient": {"$in": [name for name in recipe_ing_names]} 
                },
                {"$set": {"last_used_at": datetime.utcnow()}}
            )

    return jsonify({"message": "Meal history and stats recorded", "recipe_name": recipe_name}), 200

@app.route("/meal-history/backfill/<user_id>", methods=["POST"])
def backfill_meal_history(user_id):
    # UX Correction: Derive user_id from session first
    user_id = session.get("user_id") or user_id
    
    # Check last 50 history items where recipe_name is missing
    cursor = db.meal_history.find(
        {"user_id": user_id, "recipe_name": {"$exists": False}}
    ).sort("cooked_at", -1).limit(50)
    
    to_update = list(cursor)
    scanned = len(to_update)
    updated = 0
    
    print(f"DEBUG: Backfill Start for {user_id}. Scanned: {len(to_update)}")
    for record in to_update:
        r_id = record.get("recipe_id")
        print(f"DEBUG: Processing record {record.get('_id')}, recipe_id: '{r_id}' (Type: {type(r_id)})")
        
        if not r_id: 
            print("DEBUG: Skipping - No recipe_id")
            continue
            
        # Strategy A
        print(f"DEBUG: Lookup Strategy A (String): {{'recipe_id': '{r_id}'}}")
        found = db.recipes.find_one({"recipe_id": r_id})
        print(f"DEBUG: Strategy A Found: {bool(found)}")

        # Strategy B
        if not found:
            try:
                print(f"DEBUG: Lookup Strategy B (ObjectId): {{'_id': ObjectId('{r_id}')}}")
                found = db.recipes.find_one({"_id": ObjectId(r_id)})
                print(f"DEBUG: Strategy B Found: {bool(found)}")
            except Exception as e:
                print(f"DEBUG: Strategy B Failed (Invalid ObjectId): {e}")
        
        if found:
            r_name = found.get("name") or found.get("recipe_name") or "Unknown Recipe"
            r_cuisine = found.get("cuisine") or "Unknown"
            print(f"DEBUG: Updating record with Name: '{r_name}'")
            
            result = db.meal_history.update_one(
                {"_id": record["_id"]},
                {"$set": {
                    "recipe_name": r_name,
                    "recipe_cuisine": r_cuisine
                }}
            )
            print(f"DEBUG: Update Result Detected: {result.modified_count}")
            if result.modified_count > 0:
                updated += 1
        else:
            print("DEBUG: Recipe NOT FOUND by any strategy")
            
    return jsonify({"message": "Backfill complete", "scanned": scanned, "updated": updated}), 200
            
    return jsonify({"message": "Backfill complete", "scanned": scanned, "updated": updated}), 200

# --- Checkpoint 15: External Discovery API ---
@app.route("/discover/<user_id>", methods=["GET"])
def discover_recipes(user_id):
    # UX Correction: Derive user_id from session first
    user_id = session.get("user_id") or user_id
    season = get_current_season()
    seasonal_ings = set(SEASONAL_INGREDIENTS_MAP.get(season, []))
    external_recipes = fetch_external_recipes()
    pantry_items = list(db.pantry.find({"user_id": user_id}, {"_id": 0, "ingredient": 1}))
    pantry_ingredients = {item["ingredient"].lower() for item in pantry_items}
    
    discovery_results = []
    
    for recipe in external_recipes:
        rec_ings = recipe.get("ingredients", [])
        total = len(rec_ings)
        matched = 0
        missing = []
        seasonal_relevance = False
        
        if total == 0:
            match_percent = 0
        else:
            for ing in rec_ings:
                ing_lower = ing.lower()
                if ing_lower in pantry_ingredients:
                    matched += 1
                else:
                    missing.append(ing)
                
                if any(s_ing in ing_lower for s_ing in seasonal_ings):
                    seasonal_relevance = True

            match_percent = (matched / total) * 100
            
        discovery_results.append({
            "name": recipe.get("name"),
            "cuisine": recipe.get("cuisine"),
            "match_percent": round(match_percent, 1),
            "missing_ingredients": missing,
            "seasonal_relevance": seasonal_relevance,
            "source": recipe.get("source")
        })
        
    return jsonify({
        "season": season,
        "external_recipes": discovery_results
    }), 200

# --- Advanced Recommendation Engine ---

@app.route("/recommend/<user_id>", methods=["GET"])
def recommend_recipes(user_id):
    # UX Correction: Derive user_id from session first
    user_id = session.get("user_id") or user_id
    pantry_items = list(db.pantry.find({"user_id": user_id}, {"_id": 0, "ingredient": 1}))
    pantry_ingredients = {item["ingredient"].lower() for item in pantry_items}

    user_profile = db.users.find_one({"user_id": user_id}, {"_id": 0}) or {}
    
    user_diet = user_profile.get("diet")
    user_dietary_tags = {tag.lower() for tag in user_profile.get("dietary_tags", [])}
    user_disliked = {i.lower() for i in user_profile.get("disliked_ingredients", [])}
    user_liked = {i.lower() for i in user_profile.get("liked_ingredients", [])}
    user_cuisines = {c.lower() for c in user_profile.get("favorite_cuisines", [])}

    user_stats = db.user_behavior_stats.find_one({"user_id": user_id}, {"_id": 0}) or {}
    cuisine_freq = user_stats.get("cuisine_frequency", {})
    ingredient_freq = user_stats.get("ingredient_frequency", {})

    cutoff_date = datetime.utcnow() - timedelta(days=7)
    candidate_recent_meals = list(db.meal_history.find(
        {"user_id": user_id}
    ).sort("cooked_at", -1).limit(5))
    
    recent_meals = []
    for meal in candidate_recent_meals:
        if meal["cooked_at"] > cutoff_date:
            recent_meals.append(meal)

    recent_recipe_ids_map = {m["recipe_id"]: m["cooked_at"] for m in recent_meals} 
    
    all_recipes = list(db.recipes.find({}, {"_id": 0}))

    recent_cuisine_counts = Counter()
    for recipe in all_recipes:
        if recipe["recipe_id"] in recent_recipe_ids_map:
            c = recipe.get("cuisine")
            if c:
                recent_cuisine_counts[c.lower()] += 1

    recommendations = []

    for recipe in all_recipes:
        recipe_id = recipe.get("recipe_id")
        
        # --- FILTERS ---
        rec_diet = recipe.get("diet")
        if user_diet and rec_diet and user_diet.lower() != rec_diet.lower():
             continue

        rec_tags = {t.lower() for t in recipe.get("dietary_tags", [])}
        if not user_dietary_tags.issubset(rec_tags):
            continue

        raw_ingredients = recipe.get("ingredients", [])
        recipe_ingredient_names = []
        for ing in raw_ingredients:
            if isinstance(ing, dict):
                recipe_ingredient_names.append(ing.get("name", ""))
            else:
                recipe_ingredient_names.append(str(ing))

        if any(ing.lower() in user_disliked for ing in recipe_ingredient_names):
            continue

        # --- SCORING ---
        total_ingredients = len(recipe_ingredient_names)
        matched_ingredients_count = 0
        match_score_bonus = 0

        for ing in recipe_ingredient_names:
            ing_lower = ing.lower()
            
            pantry_match = False
            if ing_lower in pantry_ingredients:
                pantry_match = True
            else:
                 synonyms = INGREDIENT_SYNONYMS.get(ing_lower, [])
                 for syn in synonyms:
                     if syn.lower() in pantry_ingredients:
                         pantry_match = True
                         match_score_bonus += 0.5 
                         break
            
            if pantry_match:
                matched_ingredients_count += 1

            if ing_lower in user_liked:
                match_score_bonus += 1
            
            safe_key = ing.replace(".", "_") 
            if ingredient_freq.get(safe_key, 0) > 3:
                match_score_bonus += 0.2

        rec_cuisine = recipe.get("cuisine")
        rec_cuisine_lower = rec_cuisine.lower() if rec_cuisine else None
        
        if rec_cuisine_lower:
            if rec_cuisine_lower in user_cuisines:
                match_score_bonus += 1
            
            if cuisine_freq.get(rec_cuisine, 0) > 3:
                match_score_bonus += 0.5
            
            c_freq = cuisine_freq.get(rec_cuisine, 0)
            diversity_bonus = 0
            if c_freq == 0:
                diversity_bonus = 1.0
            elif c_freq < 3:
                diversity_bonus = 0.5
            
            match_score_bonus += diversity_bonus

        variety_penalty = 0
        if rec_cuisine_lower and recent_cuisine_counts[rec_cuisine_lower] > 2:
            variety_penalty = -2

        recently_cooked = False
        last_cooked_at = None
        if recipe_id in recent_recipe_ids_map:
            recently_cooked = True
            last_cooked_at = recent_recipe_ids_map[recipe_id].strftime('%Y-%m-%d')
            match_score_bonus -= 5 

        missing_count = total_ingredients - matched_ingredients_count
        if missing_count > 2:
            continue

        is_full_match = (missing_count == 0)
        final_score = matched_ingredients_count + match_score_bonus + variety_penalty
        
        rec_entry = {
            "recipe_id": recipe_id,
            "name": recipe.get("name"),
            "is_full_match": is_full_match,
            "missing_count": missing_count,
            "match_score": final_score,
            "recently_cooked": recently_cooked,
            "source": recipe.get("source", "ai" if str(recipe_id).startswith("ai_") else "user")
        }
        
        if last_cooked_at:
            rec_entry["last_cooked_at"] = last_cooked_at
            
        recommendations.append(rec_entry)

    # --- AI RECIPE INTEGRATION (BRIDGE) ---
    try:
        from ai_cook.recommendation_bridge import get_ai_recommendations
        # Fetch AI suggestions (Virtual)
        ai_recs = get_ai_recommendations(user_id, pantry_items, user_profile)
        if ai_recs:
             recommendations.extend(ai_recs)
    except ImportError:
        pass # AI module optional / missing
    except Exception as e:
        print(f"AI Bridge Error: {e}") # Non-blocking error logging

    recommendations.sort(key=lambda x: (
        x["is_full_match"], 
        not x["recently_cooked"], 
        x["match_score"]
    ), reverse=True)

    return jsonify(recommendations), 200

@app.route("/search", methods=["GET"])
def search_recipes():
    q_ingredient = request.args.get('ingredient')
    q_cuisine = request.args.get('cuisine')
    q_tag = request.args.get('dietary_tag')
    q_max_time = request.args.get('max_cook_time')
    q_quick = request.args.get('quick') == 'true'
    q_healthy = request.args.get('healthy') == 'true'
    q_budget = request.args.get('budget') == 'true'
    user_id = request.args.get('user_id')

    pantry_ingredients = set()
    if q_budget and user_id:
        pantry_items = list(db.pantry.find({"user_id": user_id}, {"_id": 0, "ingredient": 1}))
        pantry_ingredients = {item["ingredient"].lower() for item in pantry_items}
    
    all_recipes = list(db.recipes.find({}, {"_id": 0}))
    filtered_recipes = []
    
    HEALTHY_TAGS = {"low-oil", "diabetic", "high-protein", "gluten-free"}

    for recipe in all_recipes:
        rec_ingredients = recipe.get("ingredients", [])
        rec_tags = {t.lower() for t in recipe.get("dietary_tags", [])}
        rec_cuisine = recipe.get("cuisine")
        rec_time = recipe.get("cook_time")
        
        rec_ing_names = []
        for ing in rec_ingredients:
            if isinstance(ing, dict):
                rec_ing_names.append(ing.get("name", "").lower())
            else:
                rec_ing_names.append(str(ing).lower())

        if q_ingredient:
            found = False
            for name in rec_ing_names:
                if q_ingredient.lower() in name:
                    found = True
                    break
            if not found:
                continue

        if q_cuisine:
            if not rec_cuisine or rec_cuisine.lower() != q_cuisine.lower():
                continue

        if q_tag:
            if q_tag.lower() not in rec_tags:
                continue

        if q_max_time:
            try:
                time_val = int(''.join(filter(str.isdigit, str(rec_time))))
                if time_val > int(q_max_time):
                    continue
            except (ValueError, TypeError):
                continue

        if q_quick:
            try:
                time_val = int(''.join(filter(str.isdigit, str(rec_time))))
                if time_val > 20:
                    continue
            except (ValueError, TypeError):
                continue

        if q_healthy:
            if not rec_tags.intersection(HEALTHY_TAGS):
                continue

        if q_budget:
            count_condition = len(rec_ing_names) <= 5
            match_condition = False
            if user_id and pantry_ingredients:
                matched_count = sum(1 for ing in rec_ing_names if ing in pantry_ingredients)
                if len(rec_ing_names) > 0:
                    ratio = matched_count / len(rec_ing_names)
                    if ratio >= 0.60:
                        match_condition = True
            
            if not (count_condition or match_condition):
                continue

        filtered_recipes.append(recipe)

    return jsonify(filtered_recipes), 200

# --- CHECKPOINT 18/19: Evaluation & Metrics ---

@app.route("/feedback", methods=["POST"])
def submit_feedback():
    data = request.json
    user_id = data.get("user_id")
    recipe_id = data.get("recipe_id")
    rating = data.get("rating")

    if not user_id or not recipe_id or rating is None:
        return jsonify({"error": "user_id, recipe_id and rating are required"}), 400

    feedback_entry = {
        "user_id": user_id,
        "recipe_id": recipe_id,
        "rating": rating,
        "comment": data.get("comment", ""),
        "timestamp": datetime.utcnow()
    }

    db.user_feedback.insert_one(feedback_entry)
    return jsonify({"message": "Feedback submitted"}), 200

@app.route("/metrics/<user_id>", methods=["GET"])
def get_user_metrics(user_id):
    # 1. User Satisfaction (Average Rating)
    feedback_cursor = db.user_feedback.find({"user_id": user_id})
    feedback_list = list(feedback_cursor)
    avg_rating = 0
    if feedback_list:
        avg_rating = sum(f.get("rating", 0) for f in feedback_list) / len(feedback_list)

    # 2. Pantry Utilization & Waste
    pantry_items = list(db.pantry.find({"user_id": user_id}))
    total_pantry = len(pantry_items)
    expired_count = 0
    current_date = datetime.utcnow().strftime('%Y-%m-%d')
    pantry_ing_set = set()
    
    for item in pantry_items:
        ing_name = item.get("ingredient", "").lower()
        if ing_name:
            pantry_ing_set.add(ing_name)
        if item.get("expiry_date") and item["expiry_date"] < current_date:
            expired_count += 1
            
    waste_rate = 0
    pantry_utilization_rate = 0
    
    if total_pantry > 0:
        waste_rate = expired_count / total_pantry
        
        # Checkpoint 19: Use last_used_at for explicit usage check if available
        # Otherwise fallback to meal history inference
        # Explicit usage:
        explicitly_used = 0
        for item in pantry_items:
             if item.get("last_used_at"):
                 explicitly_used += 1
        
        # Inferred usage (Legacy/Fallback)
        meal_history = list(db.meal_history.find({"user_id": user_id}))
        inferred_used_counts = set()
        for meal in meal_history:
            rid = meal.get("recipe_id")
            rec = db.recipes.find_one({"recipe_id": rid})
            if rec:
                raw_ings = rec.get("ingredients", [])
                for ing in raw_ings:
                    name = ing.get("name", "") if isinstance(ing, dict) else str(ing)
                    name = name.lower()
                    if name in pantry_ing_set:
                        inferred_used_counts.add(name)
        
        inferred_used = len(inferred_used_counts)
        
        # Use whichever is higher (as last_used_at is new and might be incomplete)
        # OR just use one. Given "additive", we just improve. 
        # Requirement says "If missing -> system must still work". 
        # "Pantry utilization is inferred indirectly. No explicit tracking... Solution: Add OPTIONAL field"
        # Let's simple OR them.
        used_count = max(explicitly_used, inferred_used)
        
        pantry_utilization_rate = used_count / total_pantry

    # 3. Variety Score (Last 10 meals)
    recent_meals = list(db.meal_history.find({"user_id": user_id}).sort("cooked_at", -1).limit(10))
    unique_cuisines = set()
    total_recent = len(recent_meals)
    
    for meal in recent_meals:
        rid = meal.get("recipe_id")
        rec = db.recipes.find_one({"recipe_id": rid})
        if rec and rec.get("cuisine"):
            unique_cuisines.add(rec["cuisine"].lower())
            
    variety_score = len(unique_cuisines) / total_recent if total_recent > 0 else 0

    # 4. Recommendation Accuracy
    # Checkpoint 19: Enhanced with cooked_from_recommendation
    high_match_meals = 0
    accuracy_sample_size = len(recent_meals)
    
    for meal in recent_meals:
        # Checkpoint 19: Explicit Signal
        if meal.get("cooked_from_recommendation") is True:
             high_match_meals += 1
        else:
            # Fallback Approximation
            rid = meal.get("recipe_id")
            rec = db.recipes.find_one({"recipe_id": rid})
            if rec:
                raw_ings = rec.get("ingredients", [])
                matches = 0
                for ing in raw_ings:
                     name = ing.get("name", "") if isinstance(ing, dict) else str(ing)
                     if name.lower() in pantry_ing_set:
                         matches += 1
                
                if len(raw_ings) > 0 and (matches / len(raw_ings)) >= 0.5:
                    high_match_meals += 1
    
    recommendation_accuracy = high_match_meals / accuracy_sample_size if accuracy_sample_size > 0 else 0

    return jsonify({
        "user_id": user_id,
        "average_rating": round(avg_rating, 2),
        "pantry_utilization_rate": round(pantry_utilization_rate, 2),
        "waste_rate": round(waste_rate, 2),
        "variety_score": round(variety_score, 2),
        "recommendation_accuracy": round(recommendation_accuracy, 2)
    }), 200


# --- CHECKPOINT 20: Outcome Metrics ---
@app.route('/outcomes/<user_id>', methods=['GET'])
def get_outcomes(user_id):
    """
    CHECKPOINT 20: Outcome Metrics (Read-Only)
    Exposes value metrics: Waste Reduction, Time Savings, Variety, Personalization, Intelligence.
    Purely observational, does not modify any state.
    """
    try:
        # 1. Fetch Data
        user = db.users.find_one({"user_id": user_id})
        pantry = list(db.pantry.find({"user_id": user_id}))
        history = list(db.meal_history.find({"user_id": user_id}))
        
        # Fetch all recipes referenced in history for details (cook_time, ingredients, etc.)
        # Use set to avoid duplicates in query
        recipe_ids = list(set(h['recipe_id'] for h in history))
        # Use 'recipe_id' field as consistent with app schema
        recipes_cursor = db.recipes.find({"recipe_id": {"$in": recipe_ids}})
        recipes_map = {r['recipe_id']: r for r in recipes_cursor}

        # --- 1) Food Waste Reduction Metric ---
        # avoided_waste_count: items with last_used_at set (meaning used in a recipe)
        avoided_waste_items = [item for item in pantry if item.get('last_used_at')]
        avoided_waste_count = len(avoided_waste_items)
        
        # total_expired_items: currently expired (unused) + avoided (used)
        now_str = datetime.utcnow().strftime('%Y-%m-%d')
        expired_unused_count = 0
        for item in pantry:
            # Check if expired AND NOT used
            if not item.get('last_used_at') and item.get('expiry_date') and item['expiry_date'] < now_str:
                expired_unused_count += 1
        
        total_at_risk = avoided_waste_count + expired_unused_count
        waste_avoided_rate = round(avoided_waste_count / total_at_risk, 2) if total_at_risk > 0 else 0.0

        # --- 2) Cooking Time Savings Metric ---
        cook_times_all = []
        cook_times_quick = []
        
        for h in history:
            rid = h.get('recipe_id')
            if rid in recipes_map:
                ct = recipes_map[rid].get('cook_time', 0)
                # Ensure cook_time is a number
                try:
                    ct = float(ct)
                except (ValueError, TypeError):
                    ct = 0
                
                cook_times_all.append(ct)
                if ct <= 20:
                    cook_times_quick.append(ct)
        
        avg_cook_time_all = sum(cook_times_all) / len(cook_times_all) if cook_times_all else 0
        avg_cook_time_quick = sum(cook_times_quick) / len(cook_times_quick) if cook_times_quick else 0
        
        estimated_time_saved = max(0, avg_cook_time_all - avg_cook_time_quick)

        # --- 3) Meal Variety Improvement Metric ---
        # Sort history by cooked_at ASC
        sorted_history = sorted(history, key=lambda x: x.get('cooked_at', ''))
        
        def get_cuisine(rid):
            return recipes_map.get(rid, {}).get('cuisine', 'Unknown')

        # Baseline: First 10 meals
        baseline_slice = sorted_history[:10]
        baseline_cuisines = set(get_cuisine(h['recipe_id']) for h in baseline_slice)
        baseline_count = len(baseline_slice)
        baseline_variety = len(baseline_cuisines) / baseline_count if baseline_count > 0 else 0.0
        
        # Current: Latest 10 meals
        current_slice = sorted_history[-10:] if sorted_history else []
        current_cuisines = set(get_cuisine(h['recipe_id']) for h in current_slice)
        current_count = len(current_slice)
        current_variety = len(current_cuisines) / current_count if current_count > 0 else 0.0
        
        variety_improvement = round(current_variety - baseline_variety, 2)

        # --- 4) Personalization Effectiveness Metric ---
        match_count = 0
        total_meals_checked = 0
        
        user_diet = user.get('diet', '') if user else ''
        fav_cuisines = user.get('favorite_cuisines', []) if user else []
        liked_ingredients = user.get('liked_ingredients', []) if user else []
        liked_set = set(l.lower() for l in liked_ingredients)

        for h in history:
            rid = h.get('recipe_id')
            if rid not in recipes_map:
                continue
            
            recipe = recipes_map[rid]
            total_meals_checked += 1
            
            # Criteria: Match Favorite Cuisine OR Contain Liked Ingredient
            matches_cuisine = recipe.get('cuisine') in fav_cuisines
            
            r_ing_names = []
            for ing in recipe.get('ingredients', []):
                if isinstance(ing, dict):
                    r_ing_names.append(ing.get('name', '').lower())
                else:
                    r_ing_names.append(str(ing).lower())
            
            has_liked = any(l in r_ing_names for l in liked_set)
            
            if matches_cuisine or has_liked:
                match_count += 1
        
        personalization_effectiveness = round(match_count / total_meals_checked, 2) if total_meals_checked > 0 else 0.0

        # --- 5) System Intelligence Growth Metric ---
        # Composite of Rec Accuracy, Personalization, Diversity
        
        # Rec Accuracy (Short-term)
        high_match_count = 0
        rec_eval_window = sorted_history[-5:] 
        if rec_eval_window:
            pantry_names = set(i.get('name', '').lower() for i in pantry if not i.get('last_used_at'))
            for h in rec_eval_window:
                if h.get('cooked_from_recommendation'):
                    high_match_count += 1
                else:
                    rid = h.get('recipe_id')
                    if rid in recipes_map:
                        ing_list = recipes_map[rid].get('ingredients', [])
                        r_needs = [i.get('name', '').lower() if isinstance(i, dict) else str(i).lower() for i in ing_list]
                        if r_needs:
                            matches = sum(1 for n in r_needs if n in pantry_names)
                            if (matches / len(r_needs)) >= 0.5:
                                high_match_count += 1
            rec_accuracy = high_match_count / len(rec_eval_window)
        else:
            rec_accuracy = 0.0

        # Diversity Ratio (Unique / Total)
        unique_recipe_ids = set(h['recipe_id'] for h in history)
        diversity_ratio = len(unique_recipe_ids) / len(history) if history else 0.0
        
        intelligence_growth_score = round((rec_accuracy + personalization_effectiveness + diversity_ratio) / 3, 2)

        return jsonify({
            "food_waste_reduced": {
                "avoided_items": avoided_waste_count,
                "waste_avoided_rate": waste_avoided_rate
            },
            "time_saved": {
                "estimated_minutes": round(estimated_time_saved, 1)
            },
            "meal_variety": {
                "baseline": round(baseline_variety, 2),
                "current": round(current_variety, 2),
                "improvement": variety_improvement
            },
            "personalization_effectiveness": personalization_effectiveness,
            "intelligence_growth_score": intelligence_growth_score
        }), 200

    except Exception as e:
        print(f"Error in GET /outcomes: {e}")
        return jsonify({"error": str(e)}), 500


# --- CHECKPOINT 40: User Profile (Social/Display) ---
# New collection: user_profiles
# Rules: Add-only, strictly typed, separate from preferences

@app.route("/api/profile", methods=["GET"])
def get_social_profile():
    # 1. Derive User ID
    user_id = session.get("user_id") or request.args.get("user_id")
    if not user_id:
         return jsonify({"error": "User ID required"}), 401
         
    # 2. Fetch Social Profile
    profile = db.user_profiles.find_one({"user_id": user_id}, {"_id": 0})
    if not profile:
        profile = {
            "user_id": user_id,
            "full_name": "",
            "username": "",
            "bio": "",
            "avatar_url": "",
            "location": ""
        }
        exists = False
    else:
        exists = True

    # 3. Fetch Legacy Preferences (db.users)
    # We merge these INTO the profile response so frontend sees one unified object
    legacy_user = db.users.find_one({"user_id": user_id}, {"_id": 0}) or {}
    
    # Priority: Profile > Legacy
    # But if profile is new/empty, we want legacy values
    def get_pref(key, default):
        # If key is in profile and not empty? Or just trust profile? 
        # Requirement: "Reuse existing stored preferences if they already exist"
        # Since we are just adding this, profile might not have them yet.
        val = profile.get(key)
        if val is not None and val != "" and val != []:
            return val
        return legacy_user.get(key, default)

    # 4. Construct Response with Merged Preferences
    # Structure: Root fields + 'preferences' object (or flat? User asked for data model 'preferences: {}')
    # "DATA MODEL (inside user profile document): preferences: { ... }"
    # So we should return it structured.
    
    preferences = {
        "diet": get_pref("diet", ""),
        "favorite_cuisines": get_pref("favorite_cuisines", []),
        "dietary_tags": get_pref("dietary_tags", []),
        "liked_ingredients": get_pref("liked_ingredients", []),
        "disliked_ingredients": get_pref("disliked_ingredients", [])
    }
    
    profile["preferences"] = preferences
    
    return jsonify({"exists": exists, "profile": profile}), 200


@app.route("/api/profile", methods=["POST"])
def create_social_profile():
    return update_social_profile() # Re-use PUT logic for simplicity/upsert or maintain split if needed.
    # User said: "POST creates... PUT updates". 
    # Let's keep strict but share logic.
    # Actually, the user requirement for PUT said "Update PUT... to accept preferences".
    # I'll implement a unified upsert-like logic or separate if cleaner.
    # Let's rewrite POST to call the shared logic below.

@app.route("/api/profile", methods=["PUT"])
def update_social_profile():
    # 1. Identify User
    data = request.json
    user_id = session.get("user_id") or data.get("user_id")
    if not user_id:
        return jsonify({"error": "User ID required"}), 401

    # 2. Extract Data
    # Social Fields
    social_updates = {
        "updated_at": datetime.utcnow()
    }
    if "full_name" in data: social_updates["full_name"] = data["full_name"][:50]
    if "username" in data: social_updates["username"] = data["username"][:30]
    if "bio" in data: social_updates["bio"] = data["bio"][:160]
    if "avatar_url" in data: social_updates["avatar_url"] = data["avatar_url"]
    if "location" in data: social_updates["location"] = data["location"]

    # Preferences Fields (Expected inside 'preferences' dict or root? User said "Save calls PUT... with preferences: {...}")
    prefs = data.get("preferences", {})
    
    # Flatten prefs for storage in user_profiles (as per "DATA MODEL... inside user profile document")
    # Wait, the user said "inside user profile document: preferences: {...}". So nested.
    if prefs:
        social_updates["preferences"] = {
            "diet": prefs.get("diet", ""),
            "favorite_cuisines": prefs.get("favorite_cuisines", []),
            "dietary_tags": prefs.get("dietary_tags", []),
            "liked_ingredients": prefs.get("liked_ingredients", []),
            "disliked_ingredients": prefs.get("disliked_ingredients", [])
        }
        # Also Extract for Legacy Sync
        # We must update db.users flat fields to keep app working
        legacy_updates = {
            "diet": prefs.get("diet", ""),
            "favorite_cuisines": prefs.get("favorite_cuisines", []),
            "dietary_tags": prefs.get("dietary_tags", []),
            "liked_ingredients": prefs.get("liked_ingredients", []),
            "disliked_ingredients": prefs.get("disliked_ingredients", [])
        }
        # Sync to db.users (Legacy Storage)
        db.users.update_one({"user_id": user_id}, {"$set": legacy_updates}, upsert=True)

    # 3. Update/Insert db.user_profiles
    # Check existence
    existing = db.user_profiles.find_one({"user_id": user_id})
    if existing:
        db.user_profiles.update_one({"user_id": user_id}, {"$set": social_updates})
    else:
        # Create new
        social_updates["user_id"] = user_id
        social_updates["created_at"] = datetime.utcnow()
        if "preferences" not in social_updates and prefs:
             social_updates["preferences"] = prefs # Ensure passed prefs are saved
        db.user_profiles.insert_one(social_updates)

    # 4. Return Updated
    updated_profile = db.user_profiles.find_one({"user_id": user_id}, {"_id": 0})
    return jsonify({"message": "Profile updated", "profile": updated_profile}), 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)

