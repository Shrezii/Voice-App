from __future__ import annotations
import logging
import asyncio
import os
from dotenv import load_dotenv

from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents import Agent
from livekit.agents.llm import ChatMessage
from audio_recorder import AudioRecorder
from summarizer import summarize_transcript
from translator import detect_and_translate
from db_driver import save_summary_to_db
import whisper

load_dotenv()
logging.basicConfig(level=logging.INFO)

# Shared state
final_summary = None
full_conversation = []
full_transcript_text = None

# Whisper setup
whisper_model = whisper.load_model("base")
audio_recorder = AudioRecorder("recording.wav")

# Agent definition
agent = Agent(
    instructions="You are a bilingual clinical assistant. Listen to doctor-patient conversations and generate structured clinical summaries."
)

async def entrypoint(ctx: JobContext):
    global final_summary, full_conversation, full_transcript_text

    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    await ctx.wait_for_participant()

    audio_recorder.start()
    logging.info("🎙️ Started recording audio...")

    audio_stream = await ctx.subscribe_audio()

    async def record_audio():
        async for frame in audio_stream:
            audio_recorder.write(frame.data)

    async def record_text():
        async for msg in ctx.llm_channel:
            if isinstance(msg, ChatMessage):
                speaker = getattr(msg.sender, "identity", "unknown").capitalize()
                speaker = speaker.replace("doctor", "Doctor").replace("patient", "Patient")
                text = msg.content
                logging.info(f"[{speaker}]: {text}")
                full_conversation.append(f"{speaker}: {text}")

    await asyncio.gather(record_audio(), record_text())

    audio_recorder.stop()
    logging.info("✅ Audio saved to recording.wav")

    whisper_result = whisper_model.transcribe("recording.wav")
    transcript = whisper_result["text"]
    full_transcript_text = transcript
    logging.info("📝 Whisper Transcript:\n%s", transcript)

    english_text = detect_and_translate(transcript)
    final_summary = summarize_transcript(english_text)
    logging.info("🧠 Final Summary:\n%s", final_summary)

    save_summary_to_db(summary=final_summary, transcript=transcript, translated=english_text)
    await ctx.job.done()

# Exported functions

def get_final_summary():
    return final_summary or "No summary available"

def get_full_transcript():
    return full_transcript_text or "Transcript not available"

def reset_conversation():
    global final_summary, full_conversation, full_transcript_text
    final_summary = None
    full_conversation = []
    full_transcript_text = None

# Entry point
if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
