from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    """Application Configuration with Dynamic Multi-Subject Support"""
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    CACHE_DIR: Path = BASE_DIR / "storage" / "cache"
    TEMP_DIR: Path = BASE_DIR / "storage" / "temp"
    
    # 🆕 NEW: Dynamic Data Directories
    CATALOGS_DIR: Path = DATA_DIR / "catalogs"
    CURRICULUM_DIR: Path = DATA_DIR / "curriculum"
    INDEXES_DIR: Path = DATA_DIR / "indexes"
    
    # 🗑️ DEPRECATED (kept for backward compatibility)
    CATALOG_URL: str = "https://raw.githubusercontent.com/tutorea-ai/samacheer-kalvi-extractor/main/src/book_catalog.json"
    
    # File Management
    TEMP_FILE_RETENTION_HOURS: int = 24
    
    # AI Keys
    KIMI_API_KEY: str = ""
    KIMI_BASE_URL: str = "https://api.moonshot.ai/v1"
    KIMI_MODEL: str = "kimi-k2-0905-preview"
    
    # Bridge Path
    CONTENT_SERVER_PATH: str = ""
    
    # 🆕 NEW: Helper Methods for Dynamic Path Resolution
    
    def get_catalog_path(self, subject: str, medium: str = "english") -> Path:
        """
        Dynamically resolve catalog file path
        
        Examples:
            get_catalog_path("english") 
            → data/catalogs/languages/english.json
            
            get_catalog_path("maths", "english")
            → data/catalogs/subjects/english-medium/maths.json
            
            get_catalog_path("maths", "tamil")
            → data/catalogs/subjects/tamil-medium/maths.json
        """
        subject = subject.lower().strip()
        medium = medium.lower().strip()
        
        if subject in ["english", "tamil"]:
            # Language subjects
            return self.CATALOGS_DIR / "languages" / f"{subject}.json"
        else:
            # Other subjects (medium-specific)
            return self.CATALOGS_DIR / "subjects" / f"{medium}-medium" / f"{subject}.json"
    
    def get_curriculum_path(self, subject: str, medium: str = "english") -> Path:
        """Dynamically resolve curriculum file path"""
        subject = subject.lower().strip()
        medium = medium.lower().strip()
        
        if subject in ["english", "tamil"]:
            return self.CURRICULUM_DIR / "languages" / f"{subject}.json"
        else:
            return self.CURRICULUM_DIR / "subjects" / f"{medium}-medium" / f"{subject}.json"
    
    def get_index_path(self, subject: str, class_num: int, medium: str = "english") -> Path:
        """Dynamically resolve index file path"""
        subject = subject.lower().strip()
        medium = medium.lower().strip()
        
        if subject in ["english", "tamil"]:
            return self.INDEXES_DIR / "languages" / subject / f"class-{class_num}.json"
        else:
            return self.INDEXES_DIR / "subjects" / f"{medium}-medium" / subject / f"class-{class_num}.json"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

# Create settings instance
settings = Settings()

# Ensure directories exist
settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
settings.CATALOGS_DIR.mkdir(parents=True, exist_ok=True)
settings.CURRICULUM_DIR.mkdir(parents=True, exist_ok=True)
settings.INDEXES_DIR.mkdir(parents=True, exist_ok=True)