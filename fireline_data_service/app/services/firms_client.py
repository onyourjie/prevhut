import os
import io
import httpx
import pandas as pd
from typing import Tuple, Optional
from app.core.config import settings
from app.services.regions import region_locator

class FirmsClient:
    def __init__(self):
        self.map_key = settings.NASA_FIRMS_MAP_KEY
        self.bbox = settings.KALIMANTAN_BBOX
        self._cached_5d: Optional[pd.DataFrame] = None
        self._cache_time: Optional[float] = None

    def _normalize_df(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        if "frp" in df.columns and "frp_mw" not in df.columns:
            df["frp_mw"] = df["frp"]
        if "acq_date" in df.columns and "date" not in df.columns:
            df["date"] = df["acq_date"]
        # Provinsi & Kabupaten/Kota ditentukan dari poligon batas administrasi (point-in-polygon).
        # Titik di Sarawak/Sabah/Brunei yang ikut terambil bbox Pulau Kalimantan dibuang.
        return region_locator.annotate(df)

    async def fetch_5d_dataset(self) -> Tuple[pd.DataFrame, str]:
        """
        Ambil dataset 5 hari NASA FIRMS untuk Pulau Kalimantan (cakupan menyeluruh puluhan ribu titik).
        """
        map_key = settings.NASA_FIRMS_MAP_KEY
        if map_key == "DEMO_KEY" or not map_key:
            fallback_path = os.path.join(settings.DATA_DIR, "hotspots_kalimantan_7d.csv")
            if os.path.exists(fallback_path):
                df = pd.read_csv(fallback_path)
                return self._normalize_df(df), "Local Cache 7D (Offline Fallback)"
            return pd.DataFrame(), "No Data Available"

        try:
            url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{map_key}/VIIRS_SNPP_NRT/{self.bbox}/5"
            async with httpx.AsyncClient(timeout=25.0) as client:
                res = await client.get(url)
                if res.status_code == 200 and "latitude" in res.text:
                    df = pd.read_csv(io.StringIO(res.text))
                    df = self._normalize_df(df)
                    self._cached_5d = df
                    return df, f"NASA FIRMS VIIRS SNPP 375m (Live 5-Day - {len(df):,} Titik Kalimantan)"
        except Exception:
            pass

        # Fallback lokal jika terjadi kendala jaringan
        fallback_path = os.path.join(settings.DATA_DIR, "hotspots_kalimantan_7d.csv")
        if os.path.exists(fallback_path):
            df = pd.read_csv(fallback_path)
            return self._normalize_df(df), "Local Cache 7D (Connection Fallback)"
        return pd.DataFrame(), "No Data Available"

    async def fetch_latest_hotspots(self, target_date: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame, str]:
        """
        Ambil data titik panas satelit NASA FIRMS.
        Jika target_date diberikan (misal: '2026-10-22'), ambil data untuk tanggal tersebut.
        Mengembalikan (df_harian, df_riwayat, label_sumber).
        """
        df_history, label = await self.fetch_5d_dataset()
        if df_history.empty:
            return pd.DataFrame(), pd.DataFrame(), label

        if target_date:
            clean_date = target_date.strip()
            # Coba filter dari dataset riwayat
            if "date" in df_history.columns and clean_date in df_history["date"].values:
                df_daily = df_history[df_history["date"] == clean_date].copy()
                return df_daily, df_history, f"NASA FIRMS VIIRS SNPP ({clean_date} - {len(df_daily):,} Titik)"

            # Jika belum ada di cache, panggil langsung API NASA untuk tanggal spesifik tersebut
            map_key = settings.NASA_FIRMS_MAP_KEY
            if map_key != "DEMO_KEY" and map_key:
                try:
                    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{map_key}/VIIRS_SNPP_NRT/{self.bbox}/1/{clean_date}"
                    async with httpx.AsyncClient(timeout=20.0) as client:
                        res = await client.get(url)
                        if res.status_code == 200 and "latitude" in res.text:
                            df_fetched = pd.read_csv(io.StringIO(res.text))
                            df_fetched = self._normalize_df(df_fetched)
                            return df_fetched, df_history, f"NASA FIRMS VIIRS Live ({clean_date} - {len(df_fetched):,} Titik)"
                except Exception:
                    pass

        # Jika tidak ada target date atau tanggal tidak ditemukan, ambil tanggal terbaru yang tersedia
        if "date" in df_history.columns and not df_history["date"].empty:
            latest_date = df_history["date"].max()
            df_daily = df_history[df_history["date"] == latest_date].copy()
            # Jika tanggal terbaru titiknya sangat sedikit (< 100), gabungkan dengan tanggal sebelumnya
            if len(df_daily) < 100:
                recent_dates = df_history["date"].drop_duplicates().nlargest(2)
                df_daily = df_history[df_history["date"].isin(recent_dates)].copy()
                return df_daily, df_history, f"NASA FIRMS VIIRS SNPP (Terbaru - {len(df_daily):,} Titik)"
            return df_daily, df_history, f"NASA FIRMS VIIRS SNPP ({latest_date} - {len(df_daily):,} Titik)"

        return df_history, df_history, label

firms_client = FirmsClient()
