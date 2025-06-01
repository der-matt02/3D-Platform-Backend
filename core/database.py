from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models.quote_model import Quote
from core.config import settings

import logging
import sys

logger = logging.getLogger(__name__)


async def initiate_database():
    try:
        client = AsyncIOMotorClient(settings.MONGO_URI)
        database = client[settings.DATABASE_NAME]
        logger.info("Successfully connected to MongoDB.")
    except Exception as e:
        logger.critical(f"Failed to connect to MongoDB: {e}")
        sys.exit(1)

    try:
        await init_beanie(database=database, document_models=[Quote])
        logger.info("✅ Beanie initialized successfully with model: Quote.")
    except Exception as e:
        logger.critical(f"Failed to initialize Beanie: {e}")
        sys.exit(1)
