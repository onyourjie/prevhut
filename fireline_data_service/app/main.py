from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import clusters, hotspots, weather, community, transparency, sync

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description=settings.DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Konfigurasi CORS agar React Vite (port 5173) dan NestJS (port 3000) bisa mengakses langsung
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(clusters.router, prefix=settings.API_PREFIX)
app.include_router(hotspots.router, prefix=settings.API_PREFIX)
app.include_router(weather.router, prefix=settings.API_PREFIX)
app.include_router(community.router, prefix=settings.API_PREFIX)
app.include_router(transparency.router, prefix=settings.API_PREFIX)
app.include_router(sync.router, prefix=settings.API_PREFIX)

@app.get("/", tags=["Health & Service Info"])
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "status": "healthy",
        "documentation": "/docs",
        "endpoints": {
            "clusters": f"{settings.API_PREFIX}/clusters",
            "clusters_stats": f"{settings.API_PREFIX}/clusters/statistics",
            "hotspots_live": f"{settings.API_PREFIX}/hotspots/live",
            "weather_ispu": f"{settings.API_PREFIX}/weather-ispu",
            "community_feed": f"{settings.API_PREFIX}/community/reports",
            "transparency_kpi": f"{settings.API_PREFIX}/transparency/summary",
            "download_csv": f"{settings.API_PREFIX}/transparency/download-csv",
            "sync_live_data": f"{settings.API_PREFIX}/sync"
        }
    }
