import os
import json
from datetime import datetime
from fastapi import APIRouter
from app.services.firms_client import firms_client
from app.services.clustering import run_clustering_and_scoring
from app.services.data_loader import data_loader
from app.schemas.models import SyncResponse
from app.core.config import settings

router = APIRouter(prefix="/sync", tags=["Live Synchronization"])

@router.post("", response_model=SyncResponse)
async def sync_live_data():
    """
    Menjalankan proses sinkronisasi live data satelit NASA FIRMS dan melakukan re-clustering DBSCAN.
    Dapat dipicu oleh Cron Job Backend atau secara manual oleh Admin Posko.
    """
    df_24h, df_7d, source_label = await firms_client.fetch_latest_hotspots()
    if df_7d.empty:
        df_7d = df_24h
        
    # Re-run clustering and scoring
    new_clusters = run_clustering_and_scoring(df_24h, df_7d)
    
    # Update clusters_summary.json
    output_path = os.path.join(settings.DATA_DIR, "clusters_summary.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "title": "PREVHUT / FIRELINE Explainable Risk Clusters",
                "synced_at": datetime.now().isoformat(),
                "source": source_label,
                "total_clusters": len(new_clusters)
            },
            "clusters": new_clusters
        }, f, indent=2)
        
    # Reload cache in memory
    data_loader.reload_all()
    
    return SyncResponse(
        status="success",
        message=f"Sinkronisasi berhasil via {source_label}",
        hotspots_synced=len(df_24h),
        clusters_generated=len(new_clusters),
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S WIB")
    )
