import os
import requests
import logging

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

PROMPT = """
You are a medical assistant helping doctors summarize doctor-patient conversations.

Convert the following transcript into a structured clinical note with these sections:
Complaints, Observations, Investigations, Assessment, Treatment Plan, Past History, and Follow-Up.

Transcript:
{transcript}

Be clear and structured.
"""

def summarize_transcript(transcript: str) -> str:
    try:
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": PROMPT.format(transcript=transcript)}]
                }
            ]
        }

        response = requests.post(GEMINI_URL, json=payload, headers=headers)
        response.raise_for_status()

        result = response.json()
        summary = result["candidates"][0]["content"]["parts"][0]["text"]
        logging.info("🧠 Gemini summary generated successfully.")
        return summary.strip()

    except Exception as e:
        logging.error(f"❌ Error in summarization: {e}")
        return "Summary generation failed."