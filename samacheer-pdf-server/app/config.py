from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    CACHE_DIR: Path = BASE_DIR / "storage" / "cache"
    TEMP_DIR: Path = BASE_DIR / "storage" / "temp"
    
    # Catalog
    CATALOG_URL: str = "https://raw.githubusercontent.com/tutorea-ai/samacheer-kalvi-extractor/main/src/book_catalog.json"
    
    # File Management
    TEMP_FILE_RETENTION_HOURS: int = 24
    
    # AI Keys
    KIMI_API_KEY: str = ""
    KIMI_BASE_URL: str = "https://api.moonshot.ai/v1"
    KIMI_MODEL: str = "kimi-k2-0905-preview"
    
    # === 🌉 BRIDGE PATH (CRITICAL) ===
    CONTENT_SERVER_PATH: str = "" 
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()
settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)