from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Centroid(BaseModel):
    latitude: float
    longitude: float

class BoundingBox(BaseModel):
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float

class ClusterItem(BaseModel):
    id: str
    code: str
    kabupaten: str
    kecamatan: str
    province: str
    centroid: Centroid
    bounding_box: BoundingBox
    hotspot_count_24h: int
    days_detected_7d: int
    median_frp_mw: float
    max_frp_mw: Optional[float] = None
    base_risk_score: Optional[float] = None
    citizen_reports_count: int = 0
    citizen_urgency_boost: float = 0.0
    citizen_validation_status: Optional[str] = "Belum Ada Laporan Lapangan"
    risk_score: float
    priority_level: str
    badge: str
    nearest_settlement: Optional[str] = None
    distance_to_settlement_km: Optional[float] = None
    threat_level: Optional[str] = None
    primary_factor: str
    last_updated: str = "01.00 WIB"
    kabupaten_list: Optional[List[str]] = None
    hotspots: Optional[List[Dict[str, Any]]] = None

class HotspotPoint(BaseModel):
    id: str
    latitude: float
    longitude: float
    province: str
    brightness_kelvin: float
    confidence: str
    frp_mw: float
    date: str
    time_utc: str
    satellite: str
    daynight: str

class WeatherMonitoringStation(BaseModel):
    city: str
    province: str
    latitude: float
    longitude: float
    pm25_ug_m3: float
    ispu_value: int
    ispu_category: str
    dominant_pollutant: str
    temperature_c: Optional[float] = 31.0
    weather_desc: Optional[str] = "Cerah Berawan"

class CommunityComment(BaseModel):
    id: str
    author: str
    role: str
    content: str
    image_url: Optional[str] = None
    time_ago: str

class CommunityUpdate(BaseModel):
    id: str
    author: str
    timestamp: str
    content: str
    image_url: Optional[str] = None
    is_latest: bool = False

class CommunityReport(BaseModel):
    id: str
    author: Dict[str, Any]
    category: str
    badge_color: str
    time_ago: str
    timestamp: str
    address: str
    content: str
    image_url: Optional[str] = None
    is_live_camera: bool = True
    coordinates: Dict[str, Any]
    status: str
    status_label: str
    status_color: str
    updates_count: int = 0
    updates: List[CommunityUpdate] = []
    comments_count: int = 0
    comments: List[CommunityComment] = []

class TransparencySummary(BaseModel):
    total_hotspots_24h: int
    total_hotspots_7d: int
    total_clusters: int
    p1_clusters: int
    p2_clusters: int
    p3_clusters: int
    median_response_time_minutes: int = 24
    resolved_reports: int = 18
    pending_reports: int = 4
    updated_at: str

class SyncResponse(BaseModel):
    status: str
    message: str
    hotspots_synced: int
    clusters_generated: int
    timestamp: str
