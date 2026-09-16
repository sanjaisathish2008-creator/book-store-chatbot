import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types

from chatbot_config import CHATBOT_TITLE, SYSTEM_PROMPT

load_dotenv()

app = Flask(__name__)

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
API_KEY = os.getenv("GEMINI_API_KEY", "").strip()


def get_client():
    """Create a Gemini client only when an API request is needed."""
    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured in the .env file.")
    return genai.Client(api_key=API_KEY)


@app.get("/")
def index():
    return render_template("index.html", chatbot_title=CHATBOT_TITLE)


@app.post("/api/chat")
def chat():
    try:
        data = request.get_json(silent=True) or {}
        message = str(data.get("message", "")).strip()

        if not message:
            return jsonify({"error": "Please enter a message."}), 400

        if len(message) > 12000:
            return jsonify({"error": "Message is too long. Please keep it under 12,000 characters."}), 400

        client = get_client()

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,
            ),
        )

        answer = (response.text or "").strip()

        if not answer:
            return jsonify({"error": "Gemini returned an empty response. Please try again."}), 502

        return jsonify({"response": answer})

    except Exception as exc:
        app.logger.exception("Gemini request failed")
        return jsonify({
            "error": "Sorry, I could not process your request right now. Please check the Gemini API configuration and try again."
        }), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
