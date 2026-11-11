import time
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any, Tuple
from app.services.data_loader import data_loader
from app.services.firms_client import firms_client
from app.services.clustering import run_clustering_and_scoring
from app.schemas.models import ClusterItem

router = APIRouter(prefix="/clusters", tags=["Clusters & Priority Areas"])

# Cache in-memory untuk klaster berbasis tanggal dengan TTL 3 Jam (10.800 detik)
CLUSTER_CACHE_TTL_SECONDS = 3 * 3600
_date_clusters_cache: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}

def clear_clusters_cache():
    """Bersihkan seluruh cache klaster saat sinkronisasi 3 jam berlangsung."""
    _date_clusters_cache.clear()

def set_clusters_cache(key: str, clusters: List[Dict[str, Any]]):
    """Simpan daftar klaster ke dalam cache beserta timestamp saat ini."""
    if clusters:
        _date_clusters_cache[key] = (time.time(), list(clusters))

def _get_valid_cached_clusters(key: str) -> Optional[List[Dict[str, Any]]]:
    if key in _date_clusters_cache:
        cached_time, cached_list = _date_clusters_cache[key]
        if (time.time() - cached_time) < CLUSTER_CACHE_TTL_SECONDS and cached_list:
            return list(cached_list)
    return None

async def _get_or_compute_clusters(date: Optional[str]) -> List[Dict[str, Any]]:
    if date:
        clean_date = date.strip()
        cached = _get_valid_cached_clusters(clean_date)
        if cached is not None:
            return cached
        try:
            df_daily, df_history, _ = await firms_client.fetch_latest_hotspots(clean_date)
            if not df_daily.empty:
                computed = run_clustering_and_scoring(df_daily, df_history)
                if computed:
                    set_clusters_cache(clean_date, computed)
                    return computed
        except Exception:
            pass
        return []

    cache_key = "_latest"
    cached = _get_valid_cached_clusters(cache_key)
    if cached is not None:
        return cached
    try:
        df_daily, df_history, _ = await firms_client.fetch_latest_hotspots(None)
        if not df_daily.empty:
            computed = run_clustering_and_scoring(df_daily, df_history)
            if computed:
                set_clusters_cache(cache_key, computed)
                return computed
    except Exception:
        pass
    return data_loader.get_clusters()


@router.get("", response_model=List[ClusterItem])
async def get_clusters(
    priority: Optional[str] = Query(None, description="Filter priority (P1, P2, P3)"),
    kabupaten: Optional[str] = Query(None, description="Filter by Kabupaten (misal: Kabupaten Sintang)"),
    kecamatan: Optional[str] = Query(None, description="Filter by Kecamatan"),
    province: Optional[str] = Query(None, description="Filter by Provinsi"),
    min_score: Optional[float] = Query(None, description="Skor risiko minimal (misal: 70.0)"),
    date: Optional[str] = Query(None, description="Filter tanggal observasi satelit NASA (misal: '2026-10-22')")
):
    """
    Mengambil daftar Area Pantauan hasil pengelompokan spasial DBSCAN dan Explainable Risk Score.
    Jika parameter 'date' diberikan, klaster dihitung secara dinamis dari observasi satelit pada tanggal tersebut.
    Cache diperbarui otomatis setiap 3 jam.
    """
    clusters = list(await _get_or_compute_clusters(date))

    # Filter province
    if province:
        clean_prov = province.lower().strip()
        clusters = [c for c in clusters if clean_prov in c.get("province", "").lower()]

    # Filter kabupaten
    if kabupaten:
        clean_kab = kabupaten.lower().strip()
        clusters = [
            c for c in clusters
            if clean_kab in c.get("kabupaten", "").lower()
            or (c.get("kabupaten_list") and any(clean_kab in k.lower() for k in c["kabupaten_list"]))
        ]

    # Filter kecamatan
    if kecamatan:
        clean_kec = kecamatan.lower().strip()
        clusters = [c for c in clusters if clean_kec in c.get("kecamatan", "").lower()]

    # Filter priority (P1, P2, P3)
    if priority:
        clean_p = priority.upper().strip()
        clusters = [c for c in clusters if clean_p in c.get("priority_level", "").upper()]

    # Filter min_score
    if min_score is not None:
        clusters = [c for c in clusters if c.get("risk_score", 0) >= min_score]

    # Pastikan hasil selalu tersortir dari risiko tertinggi (P1) ke terendah (P3)
    clusters.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
    return clusters

@router.get("/statistics")
async def get_clusters_statistics(date: Optional[str] = Query(None)):
    """
    Statistik ringkasan jumlah klaster P1, P2, P3 dan total titik panas dalam klaster.
    """
    clusters = await _get_or_compute_clusters(date)

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
async def get_cluster_detail(
    cluster_id: str,
    date: Optional[str] = Query(None, description="Tanggal observasi satelit (YYYY-MM-DD)"),
):
    """
    Mengambil detail satu klaster Area Pantau pada tanggal yang diminta (atau dataset terbaru).
    """
    clean_id = cluster_id.lower().replace("-", "_")
    clusters = await _get_or_compute_clusters(date)
    for c in clusters:
        if c["id"] == clean_id or c["code"].lower().replace(" ", "_") == clean_id:
            return c

    if not date:
        cluster = data_loader.get_cluster_by_id(cluster_id)
        if cluster:
            return cluster
    raise HTTPException(status_code=404, detail=f"Area Pantau '{cluster_id}' tidak ditemukan")
