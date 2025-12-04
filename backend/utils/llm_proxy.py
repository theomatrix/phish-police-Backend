# backend/utils/llm_proxy.py

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from base64 import b64decode
from io import BytesIO
from PIL import Image

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Create a single global model (FIXES: model not defined)
model = genai.GenerativeModel("gemini-2.5-flash")


def summarize_with_llm(url, domain_info, visual_info, forms, screenshot_base64=None):

    features = {
        "url": url,
        "domain": domain_info,
        "visual": visual_info,
        "forms": forms,
    }

    # Construct prompt
    prompt = (
        "You are a cybersecurity analyst detecting phishing websites.\n"
        "Analyze the page based on:\n"
        " - URL\n"
        " - domain features\n"
        " - visual screenshot\n"
        " - forms\n"
        "Return STRICT JSON with keys: verdict, confidence, evidence.\n"
        "JSON ONLY."
    )

    inputs = [prompt, json.dumps(features, indent=2)]

    # ----- Screenshot handling -----
    if screenshot_base64:
        try:
            img_bytes = b64decode(screenshot_base64.split(",")[-1])
            image = Image.open(BytesIO(img_bytes))
            inputs.insert(1, image)
        except Exception as e:
            print("Screenshot decode error:", e)

    # ----- Call LLM -----
    try:
        response = model.generate_content(inputs)
        text = response.text.strip()
        print("Gemini raw response:", text)

        # Extract JSON
        start = text.find("{")
        end = text.rfind("}") + 1
        json_str = text[start:end]

        return json.loads(json_str)

    except Exception as e:
        print("Gemini LLM error:", e)
        return {
            "verdict": "suspicious",
            "confidence": 0.4,
            "evidence": [f"LLM error: {str(e)}"]
        }
