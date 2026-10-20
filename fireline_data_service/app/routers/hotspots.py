from fastapi import APIRouter, Query
from typing import List, Optional, Dict, Any
from app.services.data_loader import data_loader
from app.schemas.models import HotspotPoint

router = APIRouter(prefix="/hotspots", tags=["Satellite Hotspots (NASA FIRMS)"])

@router.get("/live", response_model=Dict[str, Any])
@router.get("/24h", response_model=Dict[str, Any])
def get_live_hotspots(
    province: Optional[str] = Query(None, description="Filter Provinsi (misal: Kalimantan Barat)"),
    confidence: Optional[str] = Query(None, description="Filter Confidence (nominal, high, low)"),
    limit: int = Query(500, description="Maksimal jumlah titik yang dikembalikan (default 500)")
):
    """
    Mengambil data titik panas satelit NASA FIRMS (VIIRS 375m) 24 jam terakhir.
    """
    all_hotspots = data_loader.get_hotspots_24h()
    filtered = all_hotspots
    
    if province:
        clean_prov = province.lower().strip()
        filtered = [h for h in filtered if clean_prov in h.get("province", "").lower()]
        
    if confidence:
        clean_conf = confidence.lower().strip()
        filtered = [h for h in filtered if clean_conf == h.get("confidence", "").lower()]
        
    return {
        "source": "NASA FIRMS VIIRS (Suomi-NPP 375m)",
        "period": "24 Jam Terakhir",
        "total_available": len(filtered),
        "returned": len(filtered[:limit]),
        "hotspots": filtered[:limit]
    }

@router.get("/7d", response_model=Dict[str, Any])
def get_7d_hotspots(
    province: Optional[str] = Query(None, description="Filter Provinsi"),
    limit: int = Query(500, description="Maksimal titik (default 500)")
):
    """
    Mengambil data titik panas satelit NASA FIRMS 7 hari terakhir untuk analisis tren waktu.
    """
    all_hotspots = data_loader.get_hotspots_7d()
    filtered = all_hotspots
    
    if province:
        clean_prov = province.lower().strip()
        filtered = [h for h in filtered if clean_prov in h.get("province", "").lower()]
        
    return {
        "source": "NASA FIRMS VIIRS (Suomi-NPP 375m)",
        "period": "7 Hari Terakhir",
        "total_available": len(filtered),
        "returned": len(filtered[:limit]),
        "hotspots": filtered[:limit]
    }

@router.get("/stats")
def get_hotspot_statistics():
    """
    Statistik sebaran titik panas per provinsi di Pulau Kalimantan.
    """
    all_hotspots = data_loader.get_hotspots_24h()
    prov_counts: Dict[str, int] = {}
    total_frp = 0.0
    
    for h in all_hotspots:
        p = h.get("province", "Lainnya")
        prov_counts[p] = prov_counts.get(p, 0) + 1
        total_frp += float(h.get("frp_mw", 0.0))
        
    return {
        "total_hotspots_24h": len(all_hotspots),
        "total_frp_mw": round(total_frp, 2),
        "distribution_by_province": prov_counts
    }
