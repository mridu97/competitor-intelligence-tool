from flask import Flask, request, jsonify, render_template
import anthropic
import requests
import os

app = Flask(__name__)

FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def scrape_url(url):
    try:
        response = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={"Authorization": f"Bearer {FIRECRAWL_API_KEY}"},
            json={"url": url, "formats": ["markdown"]},
            timeout=15
        )
        data = response.json()
        return data.get("data", {}).get("markdown", "")
    except:
        return ""

def analyze_competitors(competitors_data, your_product):
    combined = ""
    for name, content in competitors_data.items():
        combined += f"\n\n### {name}\n{content[:2000]}"

    prompt = f"""
    You are a senior competitive intelligence analyst.

    My product: {your_product}

    Here is scraped content from my competitors' websites:
    {combined}

    Write a competitive intelligence brief that includes:

    1. COMPETITOR SUMMARIES — For each competitor, write 2-3 sentences on what they do and how they position themselves

    2. KEY THEMES — What are all competitors focusing on? What words and messages keep appearing?

    3. GAPS & OPPORTUNITIES — What are competitors NOT talking about that could be an opportunity?

    4. MESSAGING RECOMMENDATIONS — Based on this landscape, how should my product differentiate its messaging?

    Be specific, use their actual language where relevant, and keep the whole brief under 500 words.
    """

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        your_product = data.get('your_product')
        competitors = data.get('competitors')

        competitors_data = {}
        for competitor in competitors:
            name = competitor.get('name')
            url = competitor.get('url')
            if name and url:
                scraped = scrape_url(url)
                competitors_data[name] = scraped if scraped else "Could not scrape this website."

        brief = analyze_competitors(competitors_data, your_product)
        return jsonify({"brief": brief})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 
    
    
    