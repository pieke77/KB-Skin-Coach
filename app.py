from flask import Flask, request, jsonify
import json
import re

app = Flask(__name__)

# Load product data from JSONL
products = []
with open("products.jsonl", "r") as f:
    for line in f:
        products.append(json.loads(line))

# Define synonym keywords for matching
ingredient_keywords = [
    "ascorbic acid", "vitamin c", "ethyl ascorbyl ether", "sodium ascorbyl phosphate",
    "magnesium ascorbyl phosphate", "niacinamide", "retinol", "centella asiatica",
    "hyaluronic acid", "zinc pca", "ceramide", "panthenol"
]
skin_type_keywords = ["dry", "oily", "sensitive", "normal", "combination", "acne"]
concern_keywords = [
    "anti-aging", "wrinkle", "dull", "hydration", "blemish", "pores", "redness", "elasticity"
]
product_type_keywords = ["serum", "cream", "toner", "cleanser", "ampoule", "essence"]

@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.json
    query = data.get("query", "").lower()

    if not query:
        return jsonify({"error": "No query provided."}), 400

    def matches_any(value, keywords):
        return any(kw in value for kw in keywords)

    def score(product):
        score = 0
        # Ingredients
        full_ing = product.get("full_ingredients", "").lower()
        act_ing = [ai.lower() for ai in product.get("active_ingredients", [])]
        if matches_any(full_ing, ingredient_keywords) or matches_any(" ".join(act_ing), ingredient_keywords):
            score += 3
        # Skin type
        if matches_any(" ".join(product.get("skin_types", [])).lower(), skin_type_keywords):
            score += 1
        # Concern
        if matches_any(" ".join(product.get("concerns", [])).lower(), concern_keywords):
            score += 1
        # Product type
        if matches_any(product.get("product_name", "").lower(), product_type_keywords):
            score += 1
        return score

    matched = sorted(products, key=score, reverse=True)
    top_matches = matched[:3]

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

if __name__ == "__main__":
    app.run(debug=True)
