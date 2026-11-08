import os
import json
from typing import Dict, Any, List, Optional
from app.core.config import settings

class DataLoader:
    _instance = None
    
    def __init__(self):
        self.data_dir = settings.DATA_DIR
        self._clusters_data: Dict[str, Any] = {}
        self._hotspots_24h: Dict[str, Any] = {}
        self._hotspots_7d: Dict[str, Any] = {}
        self._ispu_data: Dict[str, Any] = {}
        self._community_reports: Dict[str, Any] = {}
        self._provinces_geojson: Dict[str, Any] = {}
        self.reload_all()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = DataLoader()
        return cls._instance

    def _resolve_file(self, filename: str) -> Optional[str]:
        candidate_paths = [
            os.path.join(self.data_dir, filename),
            os.path.join(self.data_dir, "processed", filename),
            os.path.join(settings.BASE_DIR, "data", filename),
            os.path.join(settings.BASE_DIR, "data", "processed", filename),
            os.path.join(os.path.dirname(settings.BASE_DIR), "data", filename),
            os.path.join(os.path.dirname(settings.BASE_DIR), "data", "processed", filename),
        ]
        for p in candidate_paths:
            if os.path.exists(p):
                return p
        return None

    def reload_all(self):
        """Load or reload all cached JSON datasets into memory"""
        # 1. Clusters Summary
        clusters_path = self._resolve_file("clusters_summary.json")
        if clusters_path and os.path.exists(clusters_path):
            with open(clusters_path, "r", encoding="utf-8") as f:
                self._clusters_data = json.load(f)
                
        # 2. Hotspots 24h
        h24_path = self._resolve_file("hotspots_kalimantan_24h.json")
        if h24_path and os.path.exists(h24_path):
            with open(h24_path, "r", encoding="utf-8") as f:
                self._hotspots_24h = json.load(f)
                
        # 3. Hotspots 7d
        h7_path = self._resolve_file("hotspots_kalimantan_7d.json")
        if h7_path and os.path.exists(h7_path):
            with open(h7_path, "r", encoding="utf-8") as f:
                self._hotspots_7d = json.load(f)
                
        # 4. ISPU & Weather
        ispu_path = self._resolve_file("ispu_aqi_kalimantan.json")
        if ispu_path and os.path.exists(ispu_path):
            with open(ispu_path, "r", encoding="utf-8") as f:
                self._ispu_data = json.load(f)
                
        # 5. Community Reports
        comm_path = self._resolve_file("community_reports.json")
        if comm_path and os.path.exists(comm_path):
            with open(comm_path, "r", encoding="utf-8") as f:
                self._community_reports = json.load(f)
                
        # 6. Provinces GeoJSON
        geo_path = self._resolve_file("kalimantan_provinces.geojson")
        if geo_path and os.path.exists(geo_path):
            with open(geo_path, "r", encoding="utf-8") as f:
                self._provinces_geojson = json.load(f)

    def get_clusters(self) -> List[Dict[str, Any]]:
        return self._clusters_data.get("clusters", [])

    def get_cluster_by_id(self, cluster_id: str) -> Optional[Dict[str, Any]]:
        clean_id = cluster_id.lower().replace("-", "_")
        for c in self.get_clusters():
            if c["id"] == clean_id or c["code"].lower().replace(" ", "_") == clean_id:
                return c
        return None

    def get_hotspots_24h(self) -> List[Dict[str, Any]]:
        return self._hotspots_24h.get("hotspots", [])

    def get_hotspots_7d(self) -> List[Dict[str, Any]]:
        return self._hotspots_7d.get("hotspots", [])

    def get_ispu_data(self) -> Dict[str, Any]:
        return self._ispu_data

    def get_community_reports(self) -> List[Dict[str, Any]]:
        return self._community_reports.get("reports", [])

    def get_provinces_geojson(self) -> Dict[str, Any]:
        return self._provinces_geojson

data_loader = DataLoader.get_instance()
