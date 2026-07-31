from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

# Initialize module-level variables
client: AsyncIOMotorClient | None = None
db: AsyncIOMotorDatabase | None = None

async def connect() -> None:
    global client, db
    # Store Motor instance
    client = AsyncIOMotorClient(settings.MONGODB_URL.get_secret_value())
    db = client[settings.MONGODB_DB_NAME]

def disconnect() -> None:
    global client
    if client is not None:
        client.close()

def get_database() -> AsyncIOMotorDatabase:
    if db is None:
        raise RuntimeError("Database has not been initialized.")
    return db