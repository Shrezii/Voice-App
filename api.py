from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from livekit.api import LiveKitAPI, ListRoomsRequest, AccessToken, VideoGrants
import logging, asyncio, uuid, os
import threading

# Import state management functions
try:
    from Backend.agent import get_final_summary, get_full_transcript, reset_conversation
except ImportError:
    # Fallback if clinical_agent isn't available
    def get_final_summary(): return "Service unavailable"
    def get_full_transcript(): return "Service unavailable"
    def reset_conversation(): pass

# Setup app and logging
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("clinical-api")

load_dotenv()
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "wss://clinical-ai-assistant.livekit.cloud")

# Validate environment variables
if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
    logger.error("❌ Missing LIVEKIT_API_KEY or LIVEKIT_API_SECRET")
    raise ValueError("LiveKit credentials not found in environment variables")

# ---------- Health Check ----------
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Clinical AI Assistant API",
        "version": "1.0.0"
    })

# ---------- Summary Endpoints ----------
@app.route("/getSummary", methods=["GET"])
def get_summary():
    logger.info("GET /getSummary called")
    try:
        summary = get_final_summary()
        transcript = get_full_transcript()
        
        return jsonify({
            "summary": summary or "No summary generated yet.",
            "transcript": transcript or "Transcript not available.",
            "status": "success"
        })
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        return jsonify({
            "error": "Failed to retrieve summary",
            "status": "error"
        }), 500

@app.route("/resetSummary", methods=["POST"])
def reset_summary():
    try:
        reset_conversation()
        logger.info("Conversation state reset")
        return jsonify({
            "message": "Transcript and summary reset.",
            "status": "success"
        })
    except Exception as e:
        logger.error(f"Error resetting summary: {e}")
        return jsonify({
            "error": "Failed to reset summary",
            "status": "error"
        }), 500

# ---------- LiveKit Token Generation ----------
async def get_existing_room_names():
    try:
        client = LiveKitAPI(url=LIVEKIT_URL, api_key=LIVEKIT_API_KEY, api_secret=LIVEKIT_API_SECRET)
        rooms = await client.room.list_rooms(ListRoomsRequest())
        await client.aclose()
        return [room.name for room in rooms.rooms]
    except Exception as e:
        logger.error(f"Error fetching rooms: {e}")
        return []

async def generate_room_name():
    base_name = "clinical-room-" + str(uuid.uuid4())[:8]
    try:
        existing_rooms = await get_existing_room_names()
        name = base_name
        counter = 1
        while name in existing_rooms:
            name = f"{base_name}-{counter}"
            counter += 1
        return name
    except Exception as e:
        logger.error(f"Error generating room name: {e}")
        return base_name  # Fallback to base name

@app.route("/getClinicalToken", methods=["GET"])
def get_clinical_token():
    try:
        name = request.args.get("name", "doctor")
        room = request.args.get("room")

        # Validate name
        if not name or len(name.strip()) == 0:
            return jsonify({"error": "Invalid name parameter"}), 400

        # Generate room if not provided
        if not room:
            try:
                room = asyncio.run(generate_room_name())
            except Exception as e:
                logger.error(f"Error generating room: {e}")
                room = f"clinical-room-{uuid.uuid4().hex[:8]}"  # Simple fallback

        # Generate the token
        token = AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
            .with_identity(name) \
            .with_name(name) \
            .with_grants(VideoGrants(
                room_join=True,
                room=room,
                can_publish=True,
                can_subscribe=True
            ))

        jwt_token = token.to_jwt()
        
        logger.info(f"Token generated for {name} in room {room}")
        
        return jsonify({
            "token": jwt_token,
            "room": room,
            "identity": name,
            "url": LIVEKIT_URL,
            "status": "success"
        })

    except Exception as e:
        logger.error(f"Error generating token: {e}")
        return jsonify({
            "error": "Failed to generate token",
            "details": str(e),
            "status": "error"
        }), 500

# ---------- Error Handlers ----------
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found", "status": "error"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error", "status": "error"}), 500

if __name__ == "__main__":
    logger.info("🚀 Clinical AI Assistant API starting at http://localhost:5001")
    logger.info(f"🔗 LiveKit URL: {LIVEKIT_URL}")
    app.run(host="0.0.0.0", port=5001, debug=True)