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

    # Dynamic Data Directories
    CATALOGS_DIR: Path = DATA_DIR / "catalogs"
    CURRICULUM_DIR: Path = DATA_DIR / "curriculum"
    INDEXES_DIR: Path = DATA_DIR / "indexes"

    # File Management
    TEMP_FILE_RETENTION_HOURS: int = 24

    # ================================================================
    # AI — Anthropic Claude (replaced Kimi)
    # ================================================================
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"

    # ================================================================
    # Bridge — Path to Node.js Content Server root
    # ================================================================
    CONTENT_SERVER_PATH: str = ""

    # ================================================================
    # DEPRECATED — kept only for legacy fallback catalog download
    # Remove once all catalogs are local JSON files
    # ================================================================
    CATALOG_URL: str = "https://raw.githubusercontent.com/tutorea-ai/samacheer-kalvi-extractor/main/src/book_catalog.json"

    # ================================================================
    # Helper Methods — Dynamic Path Resolution
    # ================================================================

    def get_catalog_path(self, subject: str, medium: str = "english") -> Path:
        """
        Resolve catalog file path dynamically.

        Examples:
            get_catalog_path("english")
            → data/catalogs/languages/english.json

            get_catalog_path("mathematics", "english")
            → data/catalogs/subjects/english-medium/mathematics.json
        """
        subject = subject.lower().strip()
        medium = medium.lower().strip()

        if subject in ["english", "tamil"]:
            return self.CATALOGS_DIR / "languages" / f"{subject}.json"
        else:
            return self.CATALOGS_DIR / "subjects" / f"{medium}-medium" / f"{subject}.json"

    def get_curriculum_path(self, subject: str, medium: str = "english") -> Path:
        """Resolve curriculum file path dynamically."""
        subject = subject.lower().strip()
        medium = medium.lower().strip()

        if subject in ["english", "tamil"]:
            return self.CURRICULUM_DIR / "languages" / f"{subject}.json"
        else:
            return self.CURRICULUM_DIR / "subjects" / f"{medium}-medium" / f"{subject}.json"

    def get_index_path(self, subject: str, class_num: int, medium: str = "english") -> Path:
        """Resolve index file path dynamically."""
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


# Singleton instance
settings = Settings()

# Ensure required directories exist on startup
settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
settings.CATALOGS_DIR.mkdir(parents=True, exist_ok=True)
settings.CURRICULUM_DIR.mkdir(parents=True, exist_ok=True)
settings.INDEXES_DIR.mkdir(parents=True, exist_ok=True)