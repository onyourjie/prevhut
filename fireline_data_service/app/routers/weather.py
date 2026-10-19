from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from app.services.data_loader import data_loader

router = APIRouter(prefix="/weather-ispu", tags=["Weather & Air Quality (BMKG & ISPUnet)"])

@router.get("", response_model=Dict[str, Any])
def get_all_weather_stations():
    """
    Mengambil data kualitas udara (ISPU PM2.5) dan kondisi cuaca seluruh stasiun pemantau di Kalimantan.
    """
    return data_loader.get_ispu_data()

@router.get("/{city}")
def get_weather_by_city(city: str):
    """
    Mengambil data cuaca dan ISPU untuk kota tertentu (misal: Sintang, Pontianak, Palangka Raya).
    Digunakan untuk widget 'Status Wilayahmu' di Beranda Warga & Relawan.
    """
    ispu_data = data_loader.get_ispu_data()
    stations = ispu_data.get("monitoring_stations", [])
    
    clean_city = city.lower().strip()
    for s in stations:
        if clean_city in s.get("city", "").lower():
            # Add mockup weather context
            return {
                "city": s["city"],
                "province": s["province"],
                "temperature_c": 31.0,
                "weather_desc": "Cerah Berawan",
                "humidity_percent": 74,
                "wind_direction": "Tenggara",
                "ispu_value": s["ispu_value"],
                "ispu_category": s["ispu_category"],
                "dominant_pollutant": s["dominant_pollutant"],
                "health_advice": "Kualitas udara sedang. Kelompok sensitif disarankan mengurangi aktivitas luar ruang jika asap tercium."
            }
            
    # Default fallback response for Kalimantan cities
    return {
        "city": city.title(),
        "province": "Kalimantan Barat",
        "temperature_c": 31.0,
        "weather_desc": "Cerah",
        "humidity_percent": 72,
        "wind_direction": "Tenggara",
        "ispu_value": 78,
        "ispu_category": "Sedang",
        "dominant_pollutant": "PM2.5",
        "health_advice": "Kualitas udara sedang. Disarankan memakai masker jika berada dekat lokasi asap."
    }
