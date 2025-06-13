import asyncio
import logging
from dotenv import load_dotenv
from livekit.agents import Worker
from Backend.agent import entrypoint

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("clinical-worker")

async def main():
    logger.info("🚀 Starting Clinical AI Agent...")
    
    worker = Worker(entrypoint)
    await worker.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Agent stopped by user")
    except Exception as e:
        logger.error(f"❌ Agent error: {e}")