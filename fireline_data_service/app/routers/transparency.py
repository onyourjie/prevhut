import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.core.config import settings
from app.services.data_loader import data_loader
from app.schemas.models import TransparencySummary

router = APIRouter(prefix="/transparency", tags=["Public Transparency Dashboard (Fitur #5)"])

@router.get("/summary", response_model=TransparencySummary)
def get_transparency_summary():
    """
    Mengambil metrik ringkasan akuntabilitas publik:
    - Total hotspot 24 jam & 7 hari
    - Klaster prioritas (P1, P2, P3)
    - Median waktu respon petugas (24 menit)
    - Rasio penyelesaian aduan warga
    """
    clusters = data_loader.get_clusters()
    p1 = len([c for c in clusters if "P1" in c.get("priority_level", "")])
    p2 = len([c for c in clusters if "P2" in c.get("priority_level", "")])
    p3 = len([c for c in clusters if "P3" in c.get("priority_level", "")])
    
    return TransparencySummary(
        total_hotspots_24h=len(data_loader.get_hotspots_24h()),
        total_hotspots_7d=len(data_loader.get_hotspots_7d()),
        total_clusters=len(clusters),
        p1_clusters=p1,
        p2_clusters=p2,
        p3_clusters=p3,
        median_response_time_minutes=24,
        resolved_reports=18,
        pending_reports=4,
        updated_at="18 Oktober 2026, 20.00 WIB"
    )

@router.get("/download-csv")
def download_priority_areas_csv():
    """
    Fitur Unduh Data Terbuka (Open Data CSV) untuk peneliti, media, dan masyarakat umum.
    Berisi daftar 91 Area Pantau lengkap dengan skor risiko dan faktor utama pendorong.
    """
    csv_path = os.path.join(settings.DATA_DIR, "fireline_priority_areas_kalimantan.csv")
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="File CSV belum digenerate")
    return FileResponse(
        path=csv_path,
        media_type="text/csv",
        filename="fireline_priority_areas_kalimantan.csv"
    )
