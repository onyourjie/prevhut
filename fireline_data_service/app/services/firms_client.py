import os
import io
import time
import asyncio
import httpx
import pandas as pd
from typing import Tuple, Optional
from app.core.config import settings
from app.services.regions import region_locator

class FirmsClient:
    # Siklus auto-refresh 3 jam (10.800 detik) sesuai jadwal orbit downlink satelit NASA VIIRS
    CACHE_TTL_SECONDS = 3 * 3600

    def __init__(self):
        self.map_key = settings.NASA_FIRMS_MAP_KEY
        self.bbox = settings.KALIMANTAN_BBOX
        self._cached_5d: Optional[pd.DataFrame] = None
        self._cached_label: str = ""
        self._cache_time: Optional[float] = None
        # Konstelasi satelit VIIRS resolusi 375m dari NASA FIRMS (NOAA-20, NOAA-21, Suomi-NPP)
        self.satellite_sources = [
            "VIIRS_NOAA20_NRT",
            "VIIRS_NOAA21_NRT",
            "VIIRS_SNPP_NRT",
        ]

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

    async def _fetch_single_source(
        self, client: httpx.AsyncClient, source: str, days: int = 5, target_date: Optional[str] = None
    ) -> pd.DataFrame:
        map_key = settings.NASA_FIRMS_MAP_KEY
        if not map_key or map_key == "DEMO_KEY":
            return pd.DataFrame()
        try:
            if target_date:
                url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{map_key}/{source}/{self.bbox}/{days}/{target_date}"
            else:
                url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{map_key}/{source}/{self.bbox}/{days}"
            
            res = await client.get(url)
            if res.status_code == 200 and "latitude" in res.text:
                lines = res.text.strip().split("\n")
                if len(lines) > 1:  # Ada data lebih dari sekadar header CSV
                    df = pd.read_csv(io.StringIO(res.text))
                    return df
        except Exception:
            pass
        return pd.DataFrame()

    async def fetch_5d_dataset(self, force_refresh: bool = False) -> Tuple[pd.DataFrame, str]:
        """
        Ambil dataset 5 hari NASA FIRMS untuk Pulau Kalimantan.
        Mengambil dari konstelasi satelit aktif NOAA-20 & NOAA-21 (serta Suomi-NPP)
        sehingga jika salah satu sensor satelit degradasi/offline, sistem tetap mendapatkan data penuh.
        Cache diperbarui otomatis setiap 3 jam (atau saat force_refresh=True).
        """
        now = time.time()
        if (
            not force_refresh
            and self._cached_5d is not None
            and not self._cached_5d.empty
            and self._cache_time is not None
            and (now - self._cache_time) < self.CACHE_TTL_SECONDS
        ):
            return self._cached_5d.copy(), self._cached_label

        map_key = settings.NASA_FIRMS_MAP_KEY
        if map_key != "DEMO_KEY" and map_key:
            try:
                async with httpx.AsyncClient(timeout=25.0) as client:
                    # Ambil paralel dari seluruh konstelasi satelit VIIRS 375m (NOAA-20, NOAA-21, dan Suomi-NPP)
                    tasks = [
                        self._fetch_single_source(client, src, days=5)
                        for src in self.satellite_sources
                    ]
                    results = await asyncio.gather(*tasks)
                    valid_dfs = [df for df in results if not df.empty]

                    if valid_dfs:
                        df_combined = pd.concat(valid_dfs, ignore_index=True)
                        if {"latitude", "longitude", "acq_date", "acq_time"}.issubset(df_combined.columns):
                            df_combined = df_combined.drop_duplicates(
                                subset=["latitude", "longitude", "acq_date", "acq_time"]
                            )
                        df_norm = self._normalize_df(df_combined)
                        if not df_norm.empty:
                            self._cached_5d = df_norm
                            self._cached_label = f"NASA FIRMS VIIRS Live Multi-Satellite ({len(df_norm):,} Titik Kalimantan)"
                            self._cache_time = time.time()
                            return df_norm.copy(), self._cached_label
            except Exception:
                pass

        # Jika gagal kueri baru namun ada cache lama di memori, gunakan cache memori terlebih dahulu
        if self._cached_5d is not None and not self._cached_5d.empty:
            return self._cached_5d.copy(), self._cached_label

        # Fallback lokal jika terjadi kendala jaringan atau batas kuota
        candidate_fallbacks = [
            os.path.join(settings.DATA_DIR, "hotspots_kalimantan_7d.csv"),
            os.path.join(settings.BASE_DIR, "data", "processed", "hotspots_kalimantan_7d.csv"),
            os.path.join(settings.BASE_DIR, "data", "hotspots_kalimantan_7d.csv"),
            os.path.join(os.path.dirname(settings.BASE_DIR), "data", "processed", "hotspots_kalimantan_7d.csv"),
        ]
        for fallback_path in candidate_fallbacks:
            if os.path.exists(fallback_path):
                df = pd.read_csv(fallback_path)
                return self._normalize_df(df), "Local Cache 7D (Offline Fallback)"

        return pd.DataFrame(), "No Data Available"

    async def fetch_latest_hotspots(
        self, target_date: Optional[str] = None, force_refresh: bool = False
    ) -> Tuple[pd.DataFrame, pd.DataFrame, str]:
        """
        Ambil data titik panas satelit NASA FIRMS.
        Jika target_date diberikan (misal: '2026-11-08'), ambil data untuk tanggal tersebut.
        Mengembalikan (df_harian, df_riwayat, label_sumber).
        """
        df_history, label = await self.fetch_5d_dataset(force_refresh=force_refresh)
        if df_history.empty:
            return pd.DataFrame(), pd.DataFrame(), label

        if target_date:
            clean_date = target_date.strip()
            # 1. Coba saring langsung dari dataset riwayat 5 hari
            if "date" in df_history.columns and clean_date in df_history["date"].values:
                df_daily = df_history[df_history["date"] == clean_date].copy()
                return df_daily, df_history, f"NASA FIRMS VIIRS ({clean_date} - {len(df_daily):,} Titik)"

            # 2. Jika tanggal belum ada di riwayat 5 hari (misal tanggal historis lampau), kueri API NASA untuk tanggal tersebut
            map_key = settings.NASA_FIRMS_MAP_KEY
            if map_key != "DEMO_KEY" and map_key:
                try:
                    async with httpx.AsyncClient(timeout=20.0) as client:
                        tasks = [
                            self._fetch_single_source(client, src, days=1, target_date=clean_date)
                            for src in ["VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT", "VIIRS_SNPP_NRT"]
                        ]
                        results = await asyncio.gather(*tasks)
                        valid_dfs = [df for df in results if not df.empty]
                        if valid_dfs:
                            df_fetched = pd.concat(valid_dfs, ignore_index=True)
                            if {"latitude", "longitude", "acq_date", "acq_time"}.issubset(df_fetched.columns):
                                df_fetched = df_fetched.drop_duplicates(
                                    subset=["latitude", "longitude", "acq_date", "acq_time"]
                                )
                            df_fetched = self._normalize_df(df_fetched)
                            if not df_fetched.empty:
                                return df_fetched, df_history, f"NASA FIRMS VIIRS Live ({clean_date} - {len(df_fetched):,} Titik)"
                except Exception:
                    pass

            # Jika target_date telah ditentukan namun tidak ada data untuk tanggal tersebut (misal belum ada orbit satelit atau 0 hotspot),
            # kembalikan DataFrame kosong agar tidak keliru menampilkan data dari tanggal lain
            return pd.DataFrame(), df_history, f"NASA FIRMS VIIRS ({clean_date} - Tidak Ada Observasi/Titik Api)"

        # Jika target_date TIDAK ditentukan (None / default), ambil observasi tanggal terbaru yang tersedia
        if "date" in df_history.columns and not df_history["date"].empty:
            latest_date = df_history["date"].max()
            df_daily = df_history[df_history["date"] == latest_date].copy()
            # Jika tanggal terbaru titiknya sangat sedikit (< 100), gabungkan dengan tanggal sebelumnya
            if len(df_daily) < 100:
                recent_dates = df_history["date"].drop_duplicates().nlargest(2)
                df_daily = df_history[df_history["date"].isin(recent_dates)].copy()
                return df_daily, df_history, f"NASA FIRMS VIIRS (Terbaru - {len(df_daily):,} Titik)"
            return df_daily, df_history, f"NASA FIRMS VIIRS ({latest_date} - {len(df_daily):,} Titik)"

        return df_history, df_history, label

firms_client = FirmsClient()
