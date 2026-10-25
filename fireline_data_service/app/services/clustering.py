import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.cluster import DBSCAN
from typing import Dict, Any, List, Optional
from app.core.config import settings

# Pusat permukiman warga utama di Kalimantan untuk penilaian eksposur spasial & kedekatan
SETTLEMENT_CENTERS = {
    # Kalimantan Barat
    "Kecamatan Sintang": {"lat": -0.0712, "lon": 111.4981, "kab": "Kabupaten Sintang", "prov": "Kalimantan Barat"},
    "Kecamatan Sungai Tebelian": {"lat": -0.1582, "lon": 111.4125, "kab": "Kabupaten Sintang", "prov": "Kalimantan Barat"},
    "Kecamatan Sepauk": {"lat": -0.1985, "lon": 111.2312, "kab": "Kabupaten Sintang", "prov": "Kalimantan Barat"},
    "Kecamatan Dedai": {"lat": -0.2514, "lon": 111.6024, "kab": "Kabupaten Sintang", "prov": "Kalimantan Barat"},
    "Kecamatan Kelam Permai": {"lat": 0.0412, "lon": 111.6812, "kab": "Kabupaten Sintang", "prov": "Kalimantan Barat"},
    "Kecamatan Tempunak": {"lat": -0.2104, "lon": 111.3850, "kab": "Kabupaten Sintang", "prov": "Kalimantan Barat"},
    "Kecamatan Hulu Sungai": {"lat": -1.8214, "lon": 111.2014, "kab": "Kabupaten Ketapang", "prov": "Kalimantan Barat"},
    "Kecamatan Sungai Raya": {"lat": -0.1145, "lon": 109.3982, "kab": "Kabupaten Kubu Raya", "prov": "Kalimantan Barat"},
    "Kecamatan Pontianak Kota": {"lat": -0.0263, "lon": 109.3425, "kab": "Kota Pontianak", "prov": "Kalimantan Barat"},
    "Kecamatan Sambas": {"lat": 1.3614, "lon": 109.3012, "kab": "Kabupaten Sambas", "prov": "Kalimantan Barat"},
    "Kecamatan Putussibau": {"lat": 0.8621, "lon": 112.9254, "kab": "Kabupaten Kapuas Hulu", "prov": "Kalimantan Barat"},
    
    # Kalimantan Tengah
    "Kecamatan Pahandut": {"lat": -2.2078, "lon": 113.9165, "kab": "Kota Palangka Raya", "prov": "Kalimantan Tengah"},
    "Kecamatan Jekan Raya": {"lat": -2.1850, "lon": 113.8850, "kab": "Kota Palangka Raya", "prov": "Kalimantan Tengah"},
    "Kecamatan Mentawa Baru": {"lat": -2.5312, "lon": 112.9512, "kab": "Kabupaten Kotawaringin Timur", "prov": "Kalimantan Tengah"},
    "Kecamatan Arut Selatan": {"lat": -2.6854, "lon": 111.6214, "kab": "Kabupaten Kotawaringin Barat", "prov": "Kalimantan Tengah"},
    "Kecamatan Selat": {"lat": -3.0112, "lon": 114.3850, "kab": "Kabupaten Kapuas", "prov": "Kalimantan Tengah"},
    "Kecamatan Kahayan Hilir": {"lat": -2.7541, "lon": 114.2514, "kab": "Kabupaten Pulang Pisau", "prov": "Kalimantan Tengah"},
    "Kecamatan Katingan Hilir": {"lat": -1.8950, "lon": 113.3850, "kab": "Kabupaten Katingan", "prov": "Kalimantan Tengah"},
    "Kecamatan Dusun Selatan": {"lat": -1.7214, "lon": 114.8512, "kab": "Kabupaten Barito Selatan", "prov": "Kalimantan Tengah"},

    # Kalimantan Selatan
    "Kecamatan Aluh-Aluh": {"lat": -3.4512, "lon": 114.5812, "kab": "Kabupaten Banjar", "prov": "Kalimantan Selatan"},
    "Kecamatan Banjarmasin Tengah": {"lat": -3.3194, "lon": 114.5908, "kab": "Kota Banjarmasin", "prov": "Kalimantan Selatan"},
    "Kecamatan Banjarbaru Selatan": {"lat": -3.4412, "lon": 114.8312, "kab": "Kota Banjarbaru", "prov": "Kalimantan Selatan"},
    "Kecamatan Pelaihari": {"lat": -3.7954, "lon": 114.7712, "kab": "Kabupaten Tanah Laut", "prov": "Kalimantan Selatan"},
    "Kecamatan Pulau Laut Utara": {"lat": -3.2954, "lon": 116.2214, "kab": "Kabupaten Kotabaru", "prov": "Kalimantan Selatan"},

    # Kalimantan Timur
    "Kecamatan Samarinda Kota": {"lat": -0.5022, "lon": 117.1536, "kab": "Kota Samarinda", "prov": "Kalimantan Timur"},
    "Kecamatan Balikpapan Kota": {"lat": -1.2654, "lon": 116.8312, "kab": "Kota Balikpapan", "prov": "Kalimantan Timur"},
    "Kecamatan Tanjung Redeb": {"lat": 2.1524, "lon": 117.4912, "kab": "Kabupaten Berau", "prov": "Kalimantan Timur"},
    "Kecamatan Tenggarong": {"lat": -0.4215, "lon": 116.9854, "kab": "Kabupaten Kutai Kartanegara", "prov": "Kalimantan Timur"},
    "Kecamatan Sangatta Utara": {"lat": 0.4950, "lon": 117.5512, "kab": "Kabupaten Kutai Timur", "prov": "Kalimantan Timur"},
    "Kecamatan Tanah Grogot": {"lat": -1.9054, "lon": 116.2014, "kab": "Kabupaten Paser", "prov": "Kalimantan Timur"},

    # Kalimantan Utara
    "Kecamatan Tarakan Tengah": {"lat": 3.3270, "lon": 117.5965, "kab": "Kota Tarakan", "prov": "Kalimantan Utara"},
    "Kecamatan Tanjung Selor": {"lat": 2.9041, "lon": 117.3643, "kab": "Kabupaten Bulungan", "prov": "Kalimantan Utara"},
    "Kecamatan Nunukan": {"lat": 4.1357, "lon": 117.6467, "kab": "Kabupaten Nunukan", "prov": "Kalimantan Utara"},
}

def haversine_dist(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0  # Radius bumi dalam km
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat / 2.0)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return float(R * c)

def calculate_citizen_boost(report_count: int) -> float:
    if report_count == 0:
        return 0.0
    elif report_count == 1:
        return 5.0
    elif report_count <= 3:
        return 10.0
    else:
        return min(15.0, 10.0 + (report_count - 3) * 1.0)

def run_clustering_and_scoring(
    df_daily: pd.DataFrame,
    df_history: pd.DataFrame,
    community_reports: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Eksekusi clustering spasial DBSCAN dan Explainable Multi-Criteria Risk Scoring.
    Mencakup seluruh Pulau Kalimantan secara akurat dan adil.
    """
    if df_daily.empty:
        return []

    # Ambil laporan komunitas
    if community_reports is None:
        try:
            reports_path = os.path.join(settings.DATA_DIR, "community_reports.json")
            if os.path.exists(reports_path):
                with open(reports_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    community_reports = data.get("reports", [])
            else:
                community_reports = []
        except Exception:
            community_reports = []

    coords_rad = np.radians(df_daily[['latitude', 'longitude']].values)
    epsilon = 8.0 / 6371.0  # Jari-jari klaster 8 km dalam radian
    
    db = DBSCAN(eps=epsilon, min_samples=3, metric='haversine').fit(coords_rad)
    df_daily = df_daily.copy()
    df_daily['cluster_id'] = db.labels_
    
    unique_clusters = [c for c in set(db.labels_) if c != -1]
    clusters = []

    now_wib = (datetime.utcnow() + timedelta(hours=7)).strftime("%H.%M WIB")
    
    for c_id in unique_clusters:
        c_pts = df_daily[df_daily['cluster_id'] == c_id]
        count_daily = len(c_pts)
        
        cent_lat = float(c_pts['latitude'].mean())
        cent_lon = float(c_pts['longitude'].mean())
        
        min_lat = float(c_pts['latitude'].min()) - 0.015
        max_lat = float(c_pts['latitude'].max()) + 0.015
        min_lon = float(c_pts['longitude'].min()) - 0.015
        max_lon = float(c_pts['longitude'].max()) + 0.015
        
        # Multi-temporal persistence matching (cek riwayat kemunculan hari)
        if not df_history.empty and 'latitude' in df_history.columns:
            in_bbox = (
                (df_history['latitude'] >= min_lat) & (df_history['latitude'] <= max_lat) &
                (df_history['longitude'] >= min_lon) & (df_history['longitude'] <= max_lon)
            )
            days_detected = df_history[in_bbox]['date'].nunique() if in_bbox.any() else 1
            days_detected = max(1, min(7, int(days_detected)))
        else:
            days_detected = 1
        
        # Evaluasi intensitas FRP riil
        frp_col = 'frp_mw' if 'frp_mw' in c_pts.columns else ('frp' if 'frp' in c_pts.columns else None)
        if frp_col and not c_pts[frp_col].dropna().empty:
            median_frp = float(c_pts[frp_col].median())
            max_frp = float(c_pts[frp_col].max())
        else:
            median_frp = 15.0
            max_frp = 30.0

        # Wilayah administrasi klaster = mayoritas titik di dalamnya (hasil point-in-polygon)
        if 'province' in c_pts.columns and c_pts['province'].notna().any():
            prov = str(c_pts['province'].mode()[0])
        else:
            prov = "Tidak Diketahui"
        if 'kabupaten' in c_pts.columns and c_pts['kabupaten'].notna().any():
            kab_counts = c_pts['kabupaten'].value_counts()
            kabupaten = str(kab_counts.index[0])
            kabupaten_list = [str(k) for k in kab_counts.index.tolist()]
        else:
            kabupaten = "Tidak Diketahui"
            kabupaten_list = []
        
        # 1. Activity (40%): Menilai kerapatan titik api (skala dinamis dari 3 hingga 50+ titik)
        norm_act = min(100.0, 30.0 + (min(count_daily, 50) / 10.0) * 14.0)

        # 2. Persistence (35%): Konsistensi kebakaran berulang di lahan gambut
        norm_pers = min(100.0, (days_detected / 4.0) * 100.0)

        # 3. Intensity (25%): Memperhitungkan median FRP dan puncak energi termal (max FRP)
        effective_frp = max(median_frp, max_frp * 0.25)
        norm_int = min(100.0, (effective_frp / 50.0) * 100.0)
        
        base_score = round(float((0.40 * norm_act) + (0.35 * norm_pers) + (0.25 * norm_int)), 1)

        # 4. Exposure & Jarak Spasial ke Permukiman Terdekat (BIG/OpenStreetMap)
        min_d = 9999.0
        best_kec = ""
        best_center: Dict[str, Any] = {}
        kec_in_kab = ""
        kec_in_kab_d = 9999.0
        for s_name, s_pos in SETTLEMENT_CENTERS.items():
            d = haversine_dist(cent_lat, cent_lon, s_pos['lat'], s_pos['lon'])
            if d < min_d:
                min_d = d
                best_kec = s_name
                best_center = s_pos
            # Kecamatan referensi hanya diambil dari kabupaten yang sama
            if s_pos.get("kab") == kabupaten and d < kec_in_kab_d:
                kec_in_kab_d = d
                kec_in_kab = s_name

        distance_km = round(min_d, 1)
        kecamatan = kec_in_kab if kec_in_kab_d <= 30.0 else ""
        nearest_settlement = f"{best_kec} ({best_center.get('kab', '-')})" if best_kec else None

        # Titik panas riil di dalam klaster (30 titik dengan FRP tertinggi)
        hotspot_items: List[Dict[str, Any]] = []
        sort_col = frp_col if frp_col else 'latitude'
        for i, (_, row) in enumerate(c_pts.sort_values(sort_col, ascending=False).head(30).iterrows()):
            acq_time = str(row.get('acq_time', '')).split('.')[0].zfill(4) if 'acq_time' in row else ''
            conf_raw = str(row.get('confidence', '')).lower()
            conf = {'h': 'high', 'n': 'nominal', 'l': 'low'}.get(conf_raw, conf_raw or 'nominal')
            hotspot_items.append({
                "latitude": round(float(row['latitude']), 5),
                "longitude": round(float(row['longitude']), 5),
                "frp_mw": round(float(row[frp_col]), 2) if frp_col and pd.notna(row[frp_col]) else 0.0,
                "confidence": conf,
                "acq_date": str(row.get('date', row.get('acq_date', ''))),
                "acq_time_utc": f"{acq_time[:2]}:{acq_time[2:]}" if len(acq_time) == 4 else "",
                "satellite": "VIIRS S-NPP 375m" if str(row.get('satellite', 'N')) in ('N', 'Suomi NPP') else f"VIIRS {row.get('satellite')}",
                "daynight": str(row.get('daynight', '')),
            })

        # Bonus ancaman kemanusiaan (Human Threat Factor)
        proximity_urgency = 0.0
        if distance_km < 3.0:
            threat_level = "🚨 Kritis (< 3 km - Ancaman Langsung Permukiman)"
            proximity_urgency = 8.0
        elif distance_km <= 7.0:
            threat_level = "⚠️ Waspada (3 - 7 km - Bahaya Paparan Asap)"
            proximity_urgency = 4.0
        else:
            threat_level = "🛡️ Pantauan Luar (> 7 km - Area Hutan/Gambut)"

        # 5. Ground Truthing Laporan Warga (Radius 10 km)
        matching_reports = 0
        if community_reports:
            for rep in community_reports:
                coords = rep.get("coordinates", {})
                r_lat = coords.get("latitude")
                r_lon = coords.get("longitude")
                if r_lat is not None and r_lon is not None:
                    if haversine_dist(cent_lat, cent_lon, float(r_lat), float(r_lon)) <= 10.0:
                        matching_reports += 1

        citizen_boost = calculate_citizen_boost(matching_reports)
        final_score = min(100.0, round(base_score + proximity_urgency + citizen_boost, 1))

        # Status Validasi Komunitas & Penjelasan Transparan
        if matching_reports >= 2:
            citizen_validation_status = f"🔴 Dikonfirmasi {matching_reports} Laporan Darurat Warga"
            primary_factor = f"Divalidasi langsung oleh {matching_reports} laporan warga sekitar (+{citizen_boost} Poin)"
        elif matching_reports == 1:
            citizen_validation_status = "🟡 Dikonfirmasi 1 Laporan Warga Lapangan"
            primary_factor = f"Dikonfirmasi oleh 1 laporan warga terdekat (+{citizen_boost} Poin)"
        elif proximity_urgency > 0:
            citizen_validation_status = "🛡️ Belum Ada Laporan Lapangan"
            primary_factor = f"Titik api sangat dekat dengan permukiman warga ({distance_km} km)"
        else:
            citizen_validation_status = "🛡️ Belum Ada Laporan Lapangan"
            factors = {
                f"Kerapatan deteksi tinggi ({count_daily} titik panas satelit)": norm_act * 0.40,
                f"Persistensi kebakaran tinggi ({days_detected} dari 7 hari)": norm_pers * 0.35,
                f"Intensitas radiasi energi termal tinggi ({round(effective_frp, 1)} MW)": norm_int * 0.25
            }
            primary_factor = max(factors, key=factors.get)

        # Klasifikasi Tingkat Prioritas
        if final_score >= 80.0:
            p_level = "P1 - Prioritas Tinggi"
            badge = "Prioritas Tinggi"
        elif final_score >= 65.0:
            p_level = "P2 - Perhatian Meningkat"
            badge = "Perhatian Meningkat"
        else:
            p_level = "P3 - Waspada Ringan"
            badge = "Waspada Ringan"

        clusters.append({
            "cluster_id": int(c_id),
            "province": prov,
            "kabupaten": kabupaten,
            "kabupaten_list": kabupaten_list,
            "kecamatan": kecamatan,
            "hotspots": hotspot_items,
            "centroid": {"latitude": round(cent_lat, 5), "longitude": round(cent_lon, 5)},
            "bounding_box": {
                "min_lat": round(min_lat, 5),
                "max_lat": round(max_lat, 5),
                "min_lon": round(min_lon, 5),
                "max_lon": round(max_lon, 5)
            },
            "hotspot_count_24h": count_daily,
            "days_detected_7d": days_detected,
            "median_frp_mw": round(median_frp, 2),
            "max_frp_mw": round(max_frp, 2),
            "base_risk_score": base_score,
            "risk_score": final_score,
            "priority_level": p_level,
            "badge": badge,
            "primary_factor": primary_factor,
            "nearest_settlement": nearest_settlement,
            "distance_to_settlement_km": distance_km,
            "threat_level": threat_level,
            "citizen_reports_count": matching_reports,
            "citizen_urgency_boost": citizen_boost,
            "citizen_validation_status": citizen_validation_status,
            "last_updated": f"{now_wib}"
        })

    # Urutkan seluruh klaster murni berdasarkan skor risiko tertinggi
    clusters.sort(key=lambda x: x['risk_score'], reverse=True)

    # Berikan penomoran Area Pantau (Area Pantau 01, 02, dst)
    for idx, c in enumerate(clusters):
        c['code'] = f"Area Pantau {str(idx + 1).zfill(2)}"
        c['id'] = f"area_pantau_{str(idx + 1).zfill(2)}"

    return clusters
