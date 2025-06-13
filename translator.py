from deep_translator import GoogleTranslator
import logging

def detect_and_translate(text: str) -> str:
    try:
        translated = GoogleTranslator(source="auto", target="en").translate(text)
        logging.info("🌍 Translation completed.")
        return translated
    except Exception as e:
        logging.warning(f"⚠️ Translation failed, using original: {e}")
        return text
