from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from .api import router
from .models import HealthResponse
from .config import settings

# Create FastAPI app
app = FastAPI(
    title="Samacheer Kalvi PDF Extractor API",
    description="RESTful API for generating PDFs and TXT files from Tamil Nadu State Board textbooks",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration (for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api", tags=["PDF Operations"])

# Root endpoint
@app.get("/", response_model=HealthResponse)
async def root():
    """
    API Information and Health Check
    """
    return HealthResponse(
        service="Samacheer Kalvi PDF Extractor",
        status="running",
        version="1.0.0",
        timestamp=datetime.now()
    )

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Detailed health check
    """
    return HealthResponse(
        service="Samacheer Kalvi PDF Extractor",
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now()
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Run on server startup
    """
    print("=" * 60)
    print("🚀 Samacheer PDF Extractor API Starting...")
    print(f"📁 Cache Directory: {settings.CACHE_DIR}")
    print(f"📁 Temp Directory: {settings.TEMP_DIR}")
    print(f"🌐 Server: http://{settings.HOST}:{settings.PORT}")
    print(f"📚 API Docs: http://localhost:{settings.PORT}/docs")
    print("=" * 60)

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Run on server shutdown
    """
    print("\n👋 Server shutting down...")