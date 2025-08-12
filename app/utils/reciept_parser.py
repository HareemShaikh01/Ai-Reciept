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


def get_categories(instance_id):
    path = "storage/categories.csv"
    if not os.path.exists(path):
        return []

    df = pd.read_csv(path)
    df = df.dropna(subset=['id', 'name'])

    # Filter categories by instance_id
    df = df[df['instance_id'] == instance_id]
    return df.to_dict(orient='records')

def reciept_parser(img_id, instance_id):
    categories = get_categories(instance_id)
    category_list = "\n".join([f"- {cat['id']}: {cat['name']}" for cat in categories])

    path = f"storage/receipts/uploads/{img_id}"
    base64_url = image_to_base64(path)

    base_prompt = f"""
    Extract the following information from the image of a receipt:
    - A list of items with their text description, price, and either a matched category_id OR a new category_name if no match is found.
    - Vendor name (store/brand name).
    - Purchase date if available.
    - Total amount.

    Here is the list of available categories (with IDs) specific to this workspace:
    {category_list}

    Match each item to the best possible category from this list using the most relevant name.
    If a match is not found, suggest a new category by returning a "category_name" instead of "category_id".
    Never confuse total with subtotal → look for a printed 'Total' field and confirm by adding up prices. 
    If mismatch, prefer the printed total.

    Return only a raw JSON object like this (no extra text or backticks):
    {{
      "items": [
        {{ "text": "Milk", "price": 2.49, "category_id": 1 }},
        {{ "text": "Yoga Mat", "price": 15.99, "category_name": "Fitness" }}
      ],
      "vendor": "Vendor Name",
      "date": "YYYY-MM-DD",
      "total": 18.48
    }}
    """

    def call_llm(prompt):
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
        return response.choices[0].message.content

    # First attempt
    response_text = call_llm(base_prompt)
    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError:
        parsed = {}

    # Retry if items missing or empty
    if not parsed.get("items") or len(parsed.get("items", [])) < 1:
        retry_prompt = base_prompt + "\n⚠️ Your last response returned no items. Try again and ensure all visible items are extracted."
        response_text = call_llm(retry_prompt)
        try:
            parsed = json.loads(response_text)
        except json.JSONDecodeError:
            parsed = {"error": "Invalid response format"}

    return parsed
