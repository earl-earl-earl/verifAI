from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

# Initialize module-level variables
client = None
db = None

async def connect():
    global client, db
    # Store Motor instance
    client = AsyncIOMotorClient(settings.MONGODB_URL.get_secret_value())
    db = client[settings.MONGODB_DB_NAME]

def disconnect():
    global client
    client.close()

def get_database():
    return db