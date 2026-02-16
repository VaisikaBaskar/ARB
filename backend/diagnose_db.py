import os
from pymongo import MongoClient
from bson import ObjectId

def log(msg):
    print(msg)

def diagnose():
    print("START DIAGNOSIS")
    client = MongoClient("mongodb://localhost:27017/")
    db = client["ai_recipe_box"]
    
    # 1. Inspect UP TO 3 items with missing name
    cursor = db.meal_history.find({"recipe_name": {"$exists": False}}).limit(3)
    items = list(cursor)
    print(f"Found {len(items)} items missing name")

    for item in items:
        rid = item.get("recipe_id")
        print(f"REC: {rid} (Type: {type(rid)})")
        
        # A: String match
        fA = db.recipes.find_one({"recipe_id": rid})
        print(f"  Lookup 'recipe_id'=val: {bool(fA)}")
        
        # B: ObjectId match (if valid)
        fB = False
        try:
            fB = db.recipes.find_one({"_id": ObjectId(rid)})
        except:
            pass
        print(f"  Lookup '_id'=ObjectId(val): {bool(fB)}")
        
    print("END DIAGNOSIS")

if __name__ == "__main__":
    diagnose()
