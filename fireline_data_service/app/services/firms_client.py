import os
import io
import httpx
import pandas as pd
from typing import Tuple
from app.core.config import settings

class FirmsClient:
    def __init__(self):
        self.map_key = settings.NASA_FIRMS_MAP_KEY
        self.bbox = settings.KALIMANTAN_BBOX

    async def fetch_latest_hotspots(self) -> Tuple[pd.DataFrame, str]:
        """
        Fetch latest NRT hotspot data from NASA FIRMS API.
        Falls back to local cache if offline or demo key.
        """
        url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{self.map_key}/VIIRS_SNPP_NRT/{self.bbox}/1"
        
        # Cek apakah menggunakan demo key
        if self.map_key == "DEMO_KEY" or not self.map_key:
            # Gunakan data lokal terproses sebagai fallback
            fallback_path = os.path.join(settings.DATA_DIR, "hotspots_kalimantan_24h.csv")
            if os.path.exists(fallback_path):
                df = pd.read_csv(fallback_path)
                return df, "Local Cache (Offline Fallback - Verified VIIRS SNPP 375m)"
            return pd.DataFrame(), "No Data Available"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url)
                if res.status_code == 200 and "latitude" in res.text:
                    df = pd.read_csv(io.StringIO(res.text))
                    # Normalisasi kolom jika perlu
                    return df, "NASA FIRMS VIIRS NRT (Live API)"
                else:
                    # Fallback ke cache lokal
                    fallback_path = os.path.join(settings.DATA_DIR, "hotspots_kalimantan_24h.csv")
                    df = pd.read_csv(fallback_path)
                    return df, f"Local Cache (API returned {res.status_code})"
        except Exception as e:
            fallback_path = os.path.join(settings.DATA_DIR, "hotspots_kalimantan_24h.csv")
            df = pd.read_csv(fallback_path)
            return df, f"Local Cache (Connection Fallback: {str(e)[:40]})"

firms_client = FirmsClient()
