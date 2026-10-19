import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "FIRELINE Data & Intelligence Service"
    PROJECT_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    DESCRIPTION: str = (
        "Microservice penyedia kecerdasan data karhutla, clustering DBSCAN, "
        "explainable fire risk score, dan data terbuka untuk aplikasi FIRELINE."
    )
    
    # NASA FIRMS API config
    NASA_FIRMS_MAP_KEY: str = os.getenv("NASA_FIRMS_MAP_KEY", "DEMO_KEY")
    KALIMANTAN_BBOX: str = "108.5,-4.5,119.2,4.5" # Bounding box Kalimantan
    
    # Data directory
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:5173", # Vite React Frontend
        "http://localhost:3000", # NestJS Core Backend
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*"
    ]

settings = Settings()
