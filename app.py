from flask import Flask, request, jsonify
import json
import re
import openai
import os

app = Flask(__name__)

# Load product data from JSONL
products = []
with open("products.jsonl", "r") as f:
    for line in f:
        products.append(json.loads(line))

# OpenAI API Key (you must set this securely)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Define known filters
ingredient_keywords = [
    "ascorbic acid", "vitamin c", "ethyl ascorbyl ether", "sodium ascorbyl phosphate",
    "magnesium ascorbyl phosphate", "niacinamide", "retinol", "centella asiatica",
    "hyaluronic acid", "zinc pca", "ceramide", "panthenol"
]
skin_type_keywords = ["dry", "oily", "sensitive", "normal", "combination", "acne"]
concern_keywords = [
    "anti-aging", "wrinkle", "dull", "hydration", "blemish", "pores", "redness", "elasticity"
]
product_type_keywords = ["serum", "cream", "toner", "cleanser", "ampoule", "essence", "mask"]

@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.json
    query = data.get("query", "").lower()
    if not query:
        return jsonify({"error": "No query provided."}), 400

    # Ask GPT to extract structured query filters
    system_prompt = """
You are a skincare assistant. Given a customer query, extract structured fields: ingredients, skin_types, concerns, product_types. Return only JSON with those keys.
"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]

    client = openai.OpenAI()
    gpt_response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.2
    )

    filters = json.loads(gpt_response["choices"][0]["message"]["content"])

    query_ingredients = filters.get("ingredients", [])
    query_skin_types = filters.get("skin_types", [])
    query_concerns = filters.get("concerns", [])
    query_product_types = filters.get("product_types", [])

    # Score products
    def score(product):
        score = 0
        active = [i.lower() for i in product.get("active_ingredients", [])]
        full = product.get("full_ingredients", "").lower()
        if any(k.lower() in full or k.lower() in " ".join(active) for k in query_ingredients):
            score += 3
        if any(k.lower() in [s.lower() for s in product.get("skin_types", [])] for k in query_skin_types):
            score += 2
        if any(k.lower() in [c.lower() for c in product.get("concerns", [])] for k in query_concerns):
            score += 2
        if any(k.lower() in product.get("product_name", "").lower() for k in query_product_types):
            score += 1
        return score

    sorted_products = sorted(products, key=score, reverse=True)
    top_matches = sorted_products[:3]

    results = []
    for p in top_matches:
        results.append({
            "brand": p.get("brand"),
            "product_name": p.get("product_name"),
            "short_description": p.get("summary"),
            "key_ingredients": p.get("active_ingredients") or [],
            "when_to_use": p.get("recommended_use") or ""
        })

    return jsonify({"recommendations": results})

@app.route("/")
def home():
    return "KBeauté API with GPT is running!"

if __name__ == "__main__":
    app.run(debug=True)
