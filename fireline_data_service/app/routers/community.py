from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
from app.services.data_loader import data_loader
from app.schemas.models import CommunityReport

router = APIRouter(prefix="/community", tags=["Community Feed & Citizen Reports"])

@router.get("/reports", response_model=List[CommunityReport])
def get_community_reports(
    category: Optional[str] = Query(None, description="Filter kategori: 'Darurat' atau 'Informasi'"),
    status: Optional[str] = Query(None, description="Filter status: 'dalam_penanganan', 'menunggu_verifikasi', 'selesai'"),
    search: Optional[str] = Query(None, description="Pencarian kata kunci postingan")
):
    """
    Mengambil feed laporan komunitas warga dan relawan.
    Mendukung pemfilteran khusus unggahan darurat, status verifikasi, dan pencarian.
    """
    reports = data_loader.get_community_reports()
    
    if category:
        clean_cat = category.lower().strip()
        reports = [r for r in reports if clean_cat in r.get("category", "").lower()]
        
    if status:
        clean_stat = status.lower().strip()
        reports = [r for r in reports if clean_stat in r.get("status", "").lower()]
        
    if search:
        clean_q = search.lower().strip()
        reports = [
            r for r in reports
            if clean_q in r.get("content", "").lower()
            or clean_q in r.get("address", "").lower()
            or clean_q in r.get("author", {}).get("name", "").lower()
        ]
        
    return reports

@router.get("/reports/{report_id}", response_model=CommunityReport)
def get_report_detail(report_id: str):
    """
    Mengambil rincian postingan laporan lengkap dengan riwayat pembaruan progres (*update pengirim*) dan komentar warga.
    """
    reports = data_loader.get_community_reports()
    for r in reports:
        if r["id"] == report_id:
            return r
    raise HTTPException(status_code=404, detail=f"Laporan '{report_id}' tidak ditemukan")

@router.post("/reports")
def create_report(report_data: Dict[str, Any] = Body(...)):
    """
    Simulasi pembuatan laporan baru oleh warga (dengan validasi kamera perangkat).
    """
    new_report = {
        "id": f"report_{len(data_loader.get_community_reports()) + 1:02d}",
        "author": report_data.get("author", {"name": "Pengguna Baru", "role": "Warga"}),
        "category": report_data.get("category", "Informasi"),
        "badge_color": "#dc2626" if report_data.get("category") == "Darurat" else "#0d9488",
        "time_ago": "Baru saja",
        "timestamp": "18 okt 26, 20.00 WIB",
        "address": report_data.get("address", "Kabupaten Sintang, Kalimantan Barat"),
        "content": report_data.get("content", ""),
        "image_url": report_data.get("image_url", "https://images.unsplash.com/photo-1542385151-efd9000785a0?auto=format&fit=crop&w=800&q=80"),
        "is_live_camera": True,
        "coordinates": report_data.get("coordinates", {"latitude": -0.0712, "longitude": 111.4981}),
        "status": "menunggu_verifikasi",
        "status_label": "Menunggu Verifikasi",
        "status_color": "#f59e0b",
        "updates_count": 0,
        "updates": [],
        "comments_count": 0,
        "comments": []
    }
    # Append to in-memory list
    data_loader._community_reports.setdefault("reports", []).insert(0, new_report)
    return {
        "status": "success",
        "message": "Laporan berhasil dikirim dan disematkan",
        "report": new_report
    }
