import os
import csv
import json
from datetime import datetime, timedelta
from fastapi import APIRouter
from app.services.firms_client import firms_client
from app.services.clustering import run_clustering_and_scoring
from app.services.data_loader import data_loader
from app.routers.clusters import clear_clusters_cache, set_clusters_cache
from app.schemas.models import SyncResponse
from app.core.config import settings

router = APIRouter(prefix="/sync", tags=["Live Synchronization"])

@router.post("", response_model=SyncResponse)
async def sync_live_data():
    """
    Menjalankan proses sinkronisasi live data satelit NASA FIRMS dan melakukan re-clustering DBSCAN.
    Dapat dipicu oleh Cron Job Backend (Setiap 3 Jam), Background Scheduler, atau secara manual oleh Admin Posko.
    """
    df_24h, df_7d, source_label = await firms_client.fetch_latest_hotspots(force_refresh=True)
    if df_7d.empty:
        df_7d = df_24h

    # Re-run clustering and scoring jika ada titik panas
    new_clusters = []
    if not df_24h.empty and not df_7d.empty:
        new_clusters = run_clustering_and_scoring(df_24h, df_7d)

    # Perlindungan Data: Hanya perbarui berkas jika klaster berhasil dibentuk.
    # Jangan menimpa berkas jika satelit gagal merespons atau sedang pemeliharaan sensor.
    if new_clusters:
        target_dirs = list({
            settings.DATA_DIR,
            os.path.join(settings.BASE_DIR, "data"),
        })

        # 1. Perbarui clusters_summary.json
        for d in target_dirs:
            try:
                os.makedirs(d, exist_ok=True)
                output_path = os.path.join(d, "clusters_summary.json")
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
            except Exception:
                pass

        # 2. Perbarui hotspots_kalimantan_24h.json agar endpoint /hotspots/live & /transparency/summary ikut real-time
        if not df_24h.empty:
            hotspots_list = []
            for idx, (_, row) in enumerate(df_24h.iterrows(), start=1):
                acq_time_raw = str(row.get("acq_time", "")).split(".")[0].zfill(4)
                time_utc = f"{acq_time_raw[:2]}:{acq_time_raw[2:]}" if len(acq_time_raw) == 4 else ""
                conf_raw = str(row.get("confidence", "n")).lower()
                conf_label = "high" if conf_raw in ["h", "high"] else ("low" if conf_raw in ["l", "low"] else "nominal")
                sat_code = str(row.get("satellite", "N20"))
                sat_label = "VIIRS (NOAA-20)" if "20" in sat_code else ("VIIRS (NOAA-21)" if "21" in sat_code else "VIIRS (Suomi-NPP)")
                hotspots_list.append({
                    "id": f"hotspot_{idx}",
                    "latitude": round(float(row["latitude"]), 5),
                    "longitude": round(float(row["longitude"]), 5),
                    "province": str(row.get("province", "Kalimantan")),
                    "brightness_kelvin": round(float(row.get("bright_ti4", 325.0)), 2),
                    "confidence": conf_label,
                    "frp_mw": round(float(row.get("frp_mw", row.get("frp", 1.0))), 2),
                    "date": str(row.get("date", row.get("acq_date", ""))),
                    "time_utc": time_utc,
                    "satellite": sat_label,
                    "daynight": str(row.get("daynight", "D")),
                })
            for d in target_dirs:
                try:
                    h24_path = os.path.join(d, "hotspots_kalimantan_24h.json")
                    with open(h24_path, "w", encoding="utf-8") as f:
                        json.dump({
                            "source": source_label,
                            "sensor": "VIIRS 375m (NOAA-20 / NOAA-21 / S-NPP)",
                            "extracted_at": datetime.now().isoformat(),
                            "region": "Pulau Kalimantan",
                            "total_hotspots": len(hotspots_list),
                            "hotspots": hotspots_list,
                        }, f, indent=2)
                except Exception:
                    pass

        # 3. Perbarui fireline_priority_areas_kalimantan.csv untuk Open Data Download
        for d in target_dirs:
            try:
                csv_path = os.path.join(d, "fireline_priority_areas_kalimantan.csv")
                with open(csv_path, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "Area_Code", "provinsi", "Kabupaten", "Kecamatan",
                        "risk_score", "priority_level", "count_24h", "days_detected_7d",
                        "median_frp", "Permukiman_Terdekat", "Jarak_Permukiman_KM",
                        "Status_Paparan_Warga", "primary_factor"
                    ])
                    for c in new_clusters:
                        writer.writerow([
                            c.get("code", ""),
                            c.get("province", ""),
                            c.get("kabupaten", ""),
                            c.get("kecamatan", ""),
                            c.get("risk_score", 0),
                            c.get("priority_level", ""),
                            c.get("hotspot_count_24h", 0),
                            c.get("days_detected_7d", 1),
                            c.get("median_frp_mw", 0),
                            c.get("nearest_settlement", ""),
                            c.get("distance_to_settlement_km", 0),
                            c.get("threat_level", ""),
                            c.get("primary_factor", ""),
                        ])
            except Exception:
                pass

        # 4. Reload cache berkas & bersihkan cache memori klaster agar langsung terpakai
        data_loader.reload_all()
        clear_clusters_cache()
        set_clusters_cache("_latest", new_clusters)
        if not df_24h.empty and "date" in df_24h.columns and df_24h["date"].nunique() == 1:
            latest_date_str = str(df_24h["date"].max())
            set_clusters_cache(latest_date_str, new_clusters)

    existing_count = len(data_loader.get_clusters())
    total_effective = len(new_clusters) if new_clusters else existing_count
    now_wib = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S WIB")

    return SyncResponse(
        status="success",
        message=f"Sinkronisasi berhasil via {source_label} ({total_effective} area pantau)",
        hotspots_synced=len(df_24h),
        clusters_generated=total_effective,
        timestamp=now_wib
    )
