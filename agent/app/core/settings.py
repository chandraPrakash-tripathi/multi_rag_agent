from os import environ
from dotenv import load_dotenv

load_dotenv()


class Config:
    GROQ_API_KEY: str = environ.get("GROQ_API_KEY", "")  ## use local llm like llama
    DATA_PATH: str = "./data"
    LOG_LEVEL: str = environ.get("LOG_LEVEL", "DEBUG")
    SQLITE_DB_PATH: str = environ.get(
        "SQLITE_DB_PATH", "./data_setup/data/travel2.sqlite"
    )
    QDRANT_URL: str = environ.get("QDRANT_URL", "http://localhost:6333")
    RECREATE_COLLECTIONS: bool = environ.get("RECREATE_COLLECTIONS", "False")
    LIMIT_ROWS: int = environ.get("LIMIT_ROWS", "100")


def get_settings():
    return Config()
