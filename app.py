from flask import Flask, request, jsonify
import json
import re

app = Flask(__name__)

# Load product data from JSONL
products = []
with open("products.jsonl", "r") as f:
    for line in f:
        products.append(json.loads(line))

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

    # Extract tokens
    def find_matches(text, keywords):
        return [kw for kw in keywords if kw in text]

    query_ingredients = find_matches(query, ingredient_keywords)
    query_skin_types = find_matches(query, skin_type_keywords)
    query_concerns = find_matches(query, concern_keywords)
    query_product_types = find_matches(query, product_type_keywords)

    # Score products
    def score(product):
        score = 0
        # Ingredient match
        active = [i.lower() for i in product.get("active_ingredients", [])]
        full = product.get("full_ingredients", "").lower()
        if any(k in full or k in " ".join(active) for k in query_ingredients):
            score += 3
        # Skin type
        if any(k in [s.lower() for s in product.get("skin_types", [])] for k in query_skin_types):
            score += 2
        # Concerns
        if any(k in [c.lower() for c in product.get("concerns", [])] for k in query_concerns):
            score += 2
        # Product type
        if any(k in product.get("product_name", "").lower() for k in query_product_types):
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
    return "KBeauté API is running!"

if __name__ == "__main__":
    app.run(debug=True)
