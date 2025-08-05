import openai
import os
import base64
import pandas as pd
from dotenv import load_dotenv
import json

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

def image_to_base64(image_path):
    mime = image_path.split('.')[-1].lower()
    with open(image_path, "rb") as img_file:
        encoded_bytes = base64.b64encode(img_file.read())
        encoded_str = encoded_bytes.decode("utf-8")
        return f"data:image/{mime};base64,{encoded_str}"

def get_categories():
    path = "storage/categories.csv"
    df = pd.read_csv(path)
    df = df.dropna(subset=['id', 'name'])  # Make sure both columns are present
    return df.to_dict(orient='records')   # List of dicts with keys 'id' and 'name'

def reciept_parser(img_id):
    categories = get_categories()
    category_list = "\n".join([f"- {cat['id']}: {cat['name']}" for cat in categories])
    path = f"storage/receipts/uploads/{img_id}"
    base64_url = image_to_base64(path)

    prompt = f"""
Extract the following information from the image of a receipt:
- A list of items with their text description, price, and matching category ID.
- Vendor name (store/brand name).
- Purchase date if available.
- Total amount.

Here is the list of available categories (with IDs):
{category_list}

Match each item to the best possible category from this list using the most relevant name and return the matched category **ID** for each item.

Return only a raw JSON object like this and dont even include backticks or any natural languages make sure its only in the forat below:
{{
  "items": [
    {{ "text": "Milk", "price": 2.49, "category_id": 1 }},
    {{ "text": "Eggs", "price": 1.99, "category_id": 1 }}
  ],
  "vendor": "Vendor Name",
  "date": "YYYY-MM-DD",
  "total": 4.48
}}
"""

    response = openai.chat.completions.create(
        model='gpt-4o',
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": base64_url}}
                ]
            }
        ]
    )

    response_text = response.choices[0].message.content
    try:
        parsed = json.loads(response_text)
        return parsed
    except json.JSONDecodeError:
        print("Failed to parse JSON from model response")
        return {"error": "Invalid response format"}


