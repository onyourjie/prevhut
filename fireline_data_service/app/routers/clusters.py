from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from app.services.data_loader import data_loader
from app.schemas.models import ClusterItem

router = APIRouter(prefix="/clusters", tags=["Clusters & Priority Areas"])

@router.get("", response_model=List[ClusterItem])
def get_clusters(
    priority: Optional[str] = Query(None, description="Filter priority (P1, P2, P3)"),
    kabupaten: Optional[str] = Query(None, description="Filter by Kabupaten (misal: Kabupaten Sintang)"),
    kecamatan: Optional[str] = Query(None, description="Filter by Kecamatan"),
    province: Optional[str] = Query(None, description="Filter by Provinsi"),
    min_score: Optional[float] = Query(None, description="Skor risiko minimal (misal: 70.0)")
):
    """
    Mengambil daftar seluruh Area Pantauan hasil pengelompokan spasial DBSCAN dan kalkulasi Explainable Risk Score.
    Mendukung filter wilayah (Kabupaten Sintang), prioritas (P1/P2), dan skor risiko.
    """
    clusters = data_loader.get_clusters()
    
    # Filter priority
    if priority:
        clean_p = priority.upper().strip()
        clusters = [c for c in clusters if clean_p in c.get("priority_level", "").upper()]
        
    # Filter kabupaten
    if kabupaten:
        clean_kab = kabupaten.lower().strip()
        clusters = [c for c in clusters if clean_kab in c.get("kabupaten", "").lower()]
        
    # Filter kecamatan
    if kecamatan:
        clean_kec = kecamatan.lower().strip()
        clusters = [c for c in clusters if clean_kec in c.get("kecamatan", "").lower()]
        
    # Filter province
    if province:
        clean_prov = province.lower().strip()
        clusters = [c for c in clusters if clean_prov in c.get("province", "").lower()]
        
    # Filter min_score
    if min_score is not None:
        clusters = [c for c in clusters if c.get("risk_score", 0) >= min_score]
        
    return clusters

@router.get("/statistics")
def get_clusters_statistics():
    """
    Statistik ringkasan jumlah klaster P1, P2, P3 dan total titik panas dalam klaster.
    """
    clusters = data_loader.get_clusters()
    p1 = len([c for c in clusters if "P1" in c.get("priority_level", "")])
    p2 = len([c for c in clusters if "P2" in c.get("priority_level", "")])
    p3 = len([c for c in clusters if "P3" in c.get("priority_level", "")])
    total_hotspots = sum(c.get("hotspot_count_24h", 0) for c in clusters)
    
    return {
        "total_clusters": len(clusters),
        "priority_1_high": p1,
        "priority_2_medium": p2,
        "priority_3_low": p3,
        "total_clustered_hotspots": total_hotspots,
        "model_used": "DBSCAN (Haversine 8km) + Multi-Criteria Explainable Risk Scoring"
    }

@router.get("/{cluster_id}", response_model=ClusterItem)
def get_cluster_detail(cluster_id: str):
    """
    Mengambil rincian 1 Area Pantauan spesifik berdasarkan ID (misal: area_pantau_01).
    Menampilkan skor, alasan pendorong utama, jarak ke permukiman, dan bounding box.
    """
    cluster = data_loader.get_cluster_by_id(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Area Pantau '{cluster_id}' tidak ditemukan")
    return cluster
