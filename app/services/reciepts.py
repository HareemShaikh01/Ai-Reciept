import os
import pandas as pd
import uuid
import datetime
from app.utils.reciept_parser import reciept_parser
from app.utils.save_reciept_image import save_receipt_image
import json


RECIEPTS_PATH = "storage/receipts"
RECIEPT_FILE = 'receipts.json'


def upload_and_parse_reciept(instance_id, file):
    # Step 1: Save uploaded image and generate receipt_id
    receipt_id, path = save_receipt_image(file)
    img_url = path.split('\\')[1]

    # Step 2: Parse the receipt
    extracted_json = reciept_parser(img_url)

    # Ensure receipt_id is added to the extracted data
    extracted_json["receipt_id"] = receipt_id
    extracted_json["instance_id"] = instance_id

    # Step 3: Append to reciepts.json
    reciepts_json_path = os.path.join(RECIEPTS_PATH, RECIEPT_FILE)

    # Load existing receipts if file exists, else start empty
    if os.path.exists(reciepts_json_path):
        with open(reciepts_json_path, 'r') as f:
            try:
                reciept_data = json.load(f)
            except json.JSONDecodeError:
                reciept_data = []
    else:
        reciept_data = []

    reciept_data.append(extracted_json)

    # Save back to file
    with open(reciepts_json_path, 'w') as f:
        json.dump(reciept_data, f, indent=2)

    # Step 4: Append items to instance CSV
    instance_csv_path = f"storage/instances/{instance_id}.csv"
    os.makedirs(os.path.dirname(instance_csv_path), exist_ok=True)

    # Ensure required fields
    csv_rows = []
    for item in extracted_json["items"]:
        csv_rows.append({
            "date": extracted_json.get("date", ""),  # fallback to blank if missing
            "text": item["text"],
            "amount": item["price"],
            "category_id": item["category_id"],
            "receipt_id": receipt_id
        })

    # Check if CSV exists to decide header
    file_exists = os.path.exists(instance_csv_path)
    df = pd.DataFrame(csv_rows)
    df.to_csv(instance_csv_path, mode='a', header=not file_exists, index=False)

    return {"receipt_id":receipt_id,"items":extracted_json['items']}  # Optional return for further use


import os
import json

def get_parsed_reciept(reciept_id):
    path = os.path.join(RECIEPTS_PATH, RECIEPT_FILE)

    with open(path, 'r') as file:
        data = json.load(file)
    
    for reciept in data:
        if reciept.get('receipt_id') == reciept_id:
            return {"JSON":reciept,"url":f'storage/receipts/uploads/{reciept_id}.jpg'}

    return None  # If no match found
