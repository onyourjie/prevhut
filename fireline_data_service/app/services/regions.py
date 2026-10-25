"""
Reverse geocoding wilayah administrasi Kalimantan berbasis poligon batas kab/kota.

Setiap titik panas NASA FIRMS dipetakan ke Provinsi + Kabupaten/Kota tempat titik itu
benar-benar berada (point-in-polygon), bukan ke pusat permukiman terdekat.
Titik di luar wilayah Indonesia (Sarawak, Sabah, Brunei) ikut terambil oleh bounding box
Pulau Kalimantan, sehingga dibuang di sini.
"""
import json
import os
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.neighbors import KDTree

from app.core.config import settings

BOUNDARY_FILE = "kalimantan_kabkota.geojson"

# Toleransi pesisir: batas poligon kab/kota bersifat generalisasi, sehingga titik di garis pantai
# atau muara sungai bisa jatuh sedikit di luar poligon. Titik dalam radius ini tetap dihitung.
COASTAL_TOLERANCE_DEG = 0.03  # ~3,3 km

PROVINCE_ORDER = [
    "Kalimantan Barat",
    "Kalimantan Tengah",
    "Kalimantan Selatan",
    "Kalimantan Timur",
    "Kalimantan Utara",
]


class _Region:
    __slots__ = ("kabupaten", "province", "rings", "bbox")

    def __init__(self, kabupaten: str, province: str, rings: List[np.ndarray]):
        self.kabupaten = kabupaten
        self.province = province
        self.rings = rings
        all_pts = np.vstack(rings)
        self.bbox = (
            float(all_pts[:, 0].min()),
            float(all_pts[:, 1].min()),
            float(all_pts[:, 0].max()),
            float(all_pts[:, 1].max()),
        )


def _points_in_rings(lon: np.ndarray, lat: np.ndarray, rings: List[np.ndarray]) -> np.ndarray:
    """Ray casting even-odd untuk sekumpulan ring (outer + hole) secara vektor."""
    inside = np.zeros(lon.shape[0], dtype=bool)
    for ring in rings:
        x1, y1 = ring[:-1, 0], ring[:-1, 1]
        x2, y2 = ring[1:, 0], ring[1:, 1]
        # Proses per blok agar memori tetap kecil
        for start in range(0, lon.shape[0], 2048):
            px = lon[start:start + 2048, None]
            py = lat[start:start + 2048, None]
            cond = (y1 > py) != (y2 > py)
            with np.errstate(divide="ignore", invalid="ignore"):
                x_cross = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
            crossings = np.count_nonzero(cond & (px < x_cross), axis=1)
            inside[start:start + 2048] ^= (crossings % 2 == 1)
    return inside


class RegionLocator:
    def __init__(self):
        self._regions: Optional[List[_Region]] = None
        self._vertex_tree: Optional[KDTree] = None
        self._vertex_owner: Optional[np.ndarray] = None

    def _load(self) -> None:
        if self._regions is not None:
            return
        path = os.path.join(settings.DATA_DIR, BOUNDARY_FILE)
        with open(path, "r", encoding="utf-8") as f:
            geo = json.load(f)

        regions: List[_Region] = []
        vertices: List[np.ndarray] = []
        owners: List[np.ndarray] = []
        for feat in geo["features"]:
            props = feat["properties"]
            geom = feat["geometry"]
            polygons = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
            rings = [np.asarray(ring, dtype=float) for poly in polygons for ring in poly if len(ring) >= 4]
            region = _Region(props["kabupaten"], props["province"], rings)
            idx = len(regions)
            regions.append(region)
            stacked = np.vstack(rings)
            vertices.append(stacked)
            owners.append(np.full(stacked.shape[0], idx))

        all_vertices = np.vstack(vertices)
        self._regions = regions
        # KDTree pada (lat, lon) untuk toleransi pesisir
        self._vertex_tree = KDTree(all_vertices[:, ::-1])
        self._vertex_owner = np.concatenate(owners)

    def locate(self, lat: np.ndarray, lon: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Kembalikan array (province, kabupaten); None jika di luar wilayah Indonesia."""
        self._load()
        n = lat.shape[0]
        owner = np.full(n, -1, dtype=int)

        for idx, region in enumerate(self._regions):
            min_lon, min_lat, max_lon, max_lat = region.bbox
            cand = np.where(
                (owner == -1)
                & (lon >= min_lon) & (lon <= max_lon)
                & (lat >= min_lat) & (lat <= max_lat)
            )[0]
            if cand.size == 0:
                continue
            hit = _points_in_rings(lon[cand], lat[cand], region.rings)
            owner[cand[hit]] = idx

        # Toleransi pesisir untuk titik yang belum terpetakan
        missing = np.where(owner == -1)[0]
        if missing.size:
            dist, nearest = self._vertex_tree.query(np.column_stack([lat[missing], lon[missing]]), k=1)
            close = dist[:, 0] <= COASTAL_TOLERANCE_DEG
            owner[missing[close]] = self._vertex_owner[nearest[close, 0]]

        provinces = np.array([self._regions[o].province if o >= 0 else None for o in owner], dtype=object)
        kabupatens = np.array([self._regions[o].kabupaten if o >= 0 else None for o in owner], dtype=object)
        return provinces, kabupatens

    def annotate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Tambahkan kolom province & kabupaten, lalu buang titik di luar Indonesia."""
        if df.empty or "latitude" not in df.columns or "longitude" not in df.columns:
            return df
        df = df.copy()
        prov, kab = self.locate(df["latitude"].to_numpy(dtype=float), df["longitude"].to_numpy(dtype=float))
        df["province"] = prov
        df["kabupaten"] = kab
        return df[df["province"].notna()].reset_index(drop=True)

    def hierarchy(self) -> List[Dict[str, object]]:
        """Daftar Provinsi -> Kabupaten/Kota resmi (sumber tunggal untuk dropdown filter)."""
        self._load()
        grouped: Dict[str, List[str]] = {p: [] for p in PROVINCE_ORDER}
        for r in self._regions:
            grouped.setdefault(r.province, []).append(r.kabupaten)
        return [
            {"province": prov, "regencies": sorted(kabs)}
            for prov, kabs in grouped.items()
            if kabs
        ]


region_locator = RegionLocator()
