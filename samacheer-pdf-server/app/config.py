from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    """Application Configuration"""
    
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
    
    # Future AI Integration
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Ensure directories exist
settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)