# app.py
from flask import Flask, request, jsonify
import json
import os
import openai

app = Flask(__name__)

# Load product data from JSONL (only once on startup)
PRODUCTS_FILE = "products.jsonl"
with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
    PRODUCTS = [json.loads(line) for line in f if line.strip()]

# Load OpenAI key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Match vitamin C keywords
VITAMIN_C_TERMS = [
    "ascorbic acid", "ethyl ascorbyl ether", "sodium ascorbyl phosphate",
    "magnesium ascorbyl phosphate", "tetrahexyldecyl ascorbate", "vitamin c"
]

def match_products(query):
    query_lower = query.lower()
    matched = []
    for p in PRODUCTS:
        if any(term in query_lower for term in VITAMIN_C_TERMS):
            full_ingredients = p.get("full_ingredients", "").lower()
            if any(term in full_ingredients for term in VITAMIN_C_TERMS):
                matched.append(p)
        else:
            summary = p.get("summary", "").lower()
            if any(word in summary for word in query_lower.split()):
                matched.append(p)
    return matched[:5]

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    query = data.get("question")
    if not query:
        return jsonify({"error": "Missing question"}), 400

    matches = match_products(query)
    if not matches:
        return jsonify({"answer": "Sorry, no products found matching your criteria."})

    context = "\n".join([
        f"Brand: {p['brand']}\nProduct: {p['product_name']}\nDescription: {p['summary']}\nKey Ingredients: {', '.join(p.get('key_ingredients', []))}\nWhen to Use: {p.get('recommended_use', '')}"[:1000]
        for p in matches
    ])

    prompt = f"""
You are KBeauté’s AI skincare expert. Only use the product data below to answer:
{context}

Question: {query}
Return a short, clear recommendation for up to 3 products, with brand, name, key ingredients and when to use.
"""

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": "You are a precise skincare expert."},
                 {"role": "user", "content": prompt}]
    )

    answer = response["choices"][0]["message"]["content"].strip()
    return jsonify({"answer": answer})

## if __name__ == "__main__":
##     app.run(debug=True)
