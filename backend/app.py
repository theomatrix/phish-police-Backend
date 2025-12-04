from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json

load_dotenv()

app = Flask(__name__)
CORS(app)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash") 

@app.route("/analyze", methods=["POST"])
def analyze():

    # RAW LOG FOR DEBUGGING
    raw_body = request.get_data(as_text=True)
    print("\n📥 RAW REQUEST BODY:")
    print(raw_body[:800], "... [truncated] ...")   

    data = request.json or {}

    #read correct keys sent by extension
    url = data.get("url", "")
    hostname = data.get("hostname", "")
    dom = data.get("dom_signature", "")
    forms = data.get("forms", [])
    screenshot = data.get("image_b64", "") 

    print("\n📥 Parsed:")
    print("URL:", url)
    print("Hostname:", hostname)
    print("DOM Length:", len(dom))
    print("Forms:", len(forms))
    print("Screenshot Included:", bool(screenshot))

    if not url or not dom:
        return jsonify({"error": "Missing URL or DOM"}), 400

    # --- Build prompt ---
    prompt_text = f"""
    You are a phishing detection AI.

    Evaluate the following webpage:

    URL: {url}
    Hostname: {hostname}

    Forms found: {len(forms)}

    DOM content:
    {dom[:5000]}



    Explain if the site is Safe / Suspicious / Dangerous.

    Return ONLY valid JSON:
    {{
        "risk_score": <0-100>,
        "risk_label": "Safe" | "Suspicious" | "Dangerous",
        "analysis": "<short explanation>"
        "screenshot": "short points about the screenshot if included and mention any red flags found while analysing the screenshot"
    }}
    """
    
    try:
        content = [prompt_text]
        if screenshot:
            try:
                import base64
                from io import BytesIO
                from PIL import Image

                # Remove header if present (e.g., "data:image/jpeg;base64,")
                if "," in screenshot:
                    screenshot = screenshot.split(",")[1]
                
                image_data = base64.b64decode(screenshot)
                image = Image.open(BytesIO(image_data))
                content.append(image)
                print("📸 Image added to Gemini prompt")
            except Exception as img_err:
                print("⚠️ Failed to process image:", img_err)

        response = model.generate_content(content)
        print("\n📤 Gemini Raw Response:\n", response.text)

        #Clean the response text before parsing
        # Remove markdown fences and any leading/trailing whitespace
        clean_text = response.text.strip().lstrip("```json").rstrip("```").strip()

        # Attempt JSON parse on the CLEANED text
        try:
            parsed = json.loads(clean_text)
        except Exception as e:
            print(f"❌ Failed to parse JSON even after cleaning: {e}")
            print(f"Cleaned text was: {clean_text}")
            parsed = {
                "risk_score": 50,
                "risk_label": "Suspicious",
                "analysis": "Model did not return valid JSON. Fallback."
            }

        return jsonify(parsed)

    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/")
def home():
    return "Phishing Analyzer Running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)