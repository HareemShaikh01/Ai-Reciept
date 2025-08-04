import os
import uuid
from datetime import datetime, timezone
import pandas as pd

# Constants
STORAGE_DIR = "storage/instances"
META_FILE = "meta.json"

# Ensure the storage directory exists
os.makedirs(STORAGE_DIR, exist_ok=True)

# Dummy function to simulate extracting user ID from token
def extract_user_id(token):
    return token  


def rename_category(token, cat_id, data):
    user_id = extract_user_id(token)

    # File paths
    meta_path = os.path.join(STORAGE_DIR, META_FILE)
    categories_path = os.path.join(STORAGE_DIR, "categories.csv")

    # Load metadata and categories
    if not os.path.exists(meta_path) or not os.path.exists(categories_path):
        return {"error": "Metadata or category data missing"}, 500

    meta_df = pd.read_json(meta_path)
    cat_df = pd.read_csv(categories_path)

    # Step 1: Locate category
    cat_row = cat_df[cat_df["id"] == int(cat_id)]
    if cat_row.empty:
        return {"error": "Category not found"}, 404

    instance_id = cat_row.iloc[0]["instance_id"]

    # Step 2: Verify user owns the instance
    workspace_row = meta_df[meta_df["instance_id"] == instance_id]
    if workspace_row.empty or workspace_row.iloc[0]["user_id"] != user_id:
        return {"error": "Forbidden"}, 403

    # Step 3: Validate input
    new_name = data.get("name", "").strip()
    if not new_name:
        return {"error": "Missing category name"}, 400

    # Step 4: Update name
    idx = cat_row.index[0]
    cat_df.at[idx, "name"] = new_name

    # Step 5: Save back to file
    cat_df.to_csv(categories_path, index=False)

    # Step 6: Return updated category
    return {"id": int(cat_id), "name": new_name}, 200


def delete_category(token, cat_id):
    user_id = extract_user_id(token)

    CATEGORIES_PATH = os.path.join(STORAGE_DIR, "categories.csv")
    META_PATH = os.path.join(STORAGE_DIR, META_FILE)

    # Step 1: Load category data
    if not os.path.exists(CATEGORIES_PATH):
        return {"error": "No categories found"}, 500
    cat_df = pd.read_csv(CATEGORIES_PATH)

    # Step 2: Ensure category exists
    try:
        cat_id = int(cat_id)
    except ValueError:
        return {"error": "Invalid category ID"}, 400

    category_row = cat_df[cat_df["id"] == cat_id]
    if category_row.empty:
        return {"error": "Category not found"}, 404

    instance_id = category_row.iloc[0]["instance_id"]

    # Step 3: Verify ownership
    if not os.path.exists(META_PATH):
        return {"error": "Metadata not found"}, 500
    meta_df = pd.read_json(META_PATH)
    workspace_row = meta_df[meta_df["instance_id"] == instance_id]

    if workspace_row.empty or workspace_row.iloc[0]["user_id"] != user_id:
        return {"error": "Forbidden"}, 403

    # Step 4: Check at least one category remains after deletion
    instance_categories = cat_df[cat_df["instance_id"] == instance_id]
    if len(instance_categories) <= 1:
        return {"error": "Cannot delete last category"}, 400


    # PENDING
    # Step 5: Update CSV file to replace deleted category with 0
    # instance_csv_path = os.path.join(STORAGE_DIR, f"{instance_id}.csv")
    # if os.path.exists(instance_csv_path):
    #     df = pd.read_csv(instance_csv_path)
    #     df["category_id"] = df["category_id"].apply(lambda x: 0 if x == cat_id else x)
    #     df.to_csv(instance_csv_path, index=False)

    # Step 6: Remove category row
    cat_df = cat_df[cat_df["id"] != cat_id]
    cat_df.to_csv(CATEGORIES_PATH, index=False)

    # Step 7: Done
    return {"deleted": True}, 200

