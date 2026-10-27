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
    # --- Kalimantan Barat ---
    # Kabupaten Sintang
    "Kecamatan Sintang": {"lat": -0.0712, "lon": 111.4981, "kab": "Kabupaten Sintang", "prov": "Kalimantan Barat"},
    "Kecamatan Sungai Tebelian": {"lat": -0.1582, "lon": 111.4125, "kab": "Kabupaten Sintang", "prov": "Kalimantan Barat"},
    "Kecamatan Sepauk": {"lat": -0.1985, "lon": 111.2312, "kab": "Kabupaten Sintang", "prov": "Kalimantan Barat"},
    "Kecamatan Dedai": {"lat": -0.1500, "lon": 111.6200, "kab": "Kabupaten Sintang", "prov": "Kalimantan Barat"},
    "Kecamatan Kelam Permai": {"lat": 0.0412, "lon": 111.6812, "kab": "Kabupaten Sintang", "prov": "Kalimantan Barat"},
    "Kecamatan Tempunak": {"lat": -0.2104, "lon": 111.3850, "kab": "Kabupaten Sintang", "prov": "Kalimantan Barat"},
    "Kecamatan Kayan Hilir": {"lat": -0.1800, "lon": 112.0500, "kab": "Kabupaten Sintang", "prov": "Kalimantan Barat"},
    # Kota Pontianak
    "Kecamatan Pontianak Kota": {"lat": -0.0263, "lon": 109.3425, "kab": "Kota Pontianak", "prov": "Kalimantan Barat"},
    "Kecamatan Pontianak Selatan": {"lat": -0.0450, "lon": 109.3300, "kab": "Kota Pontianak", "prov": "Kalimantan Barat"},
    "Kecamatan Pontianak Barat": {"lat": -0.0150, "lon": 109.3100, "kab": "Kota Pontianak", "prov": "Kalimantan Barat"},
    # Kabupaten Kubu Raya
    "Kecamatan Sungai Raya": {"lat": -0.1145, "lon": 109.3982, "kab": "Kabupaten Kubu Raya", "prov": "Kalimantan Barat"},
    "Kecamatan Rasau Jaya": {"lat": -0.2500, "lon": 109.3500, "kab": "Kabupaten Kubu Raya", "prov": "Kalimantan Barat"},
    "Kecamatan Sungai Ambawang": {"lat": -0.0300, "lon": 109.4500, "kab": "Kabupaten Kubu Raya", "prov": "Kalimantan Barat"},
    # Kabupaten Ketapang
    "Kecamatan Delta Pawan": {"lat": -1.8465, "lon": 109.9714, "kab": "Kabupaten Ketapang", "prov": "Kalimantan Barat"},
    "Kecamatan Matan Hilir Selatan": {"lat": -2.0500, "lon": 110.1500, "kab": "Kabupaten Ketapang", "prov": "Kalimantan Barat"},
    "Kecamatan Kendawangan": {"lat": -2.5500, "lon": 110.2200, "kab": "Kabupaten Ketapang", "prov": "Kalimantan Barat"},
    "Kecamatan Singkup": {"lat": -2.6500, "lon": 110.6500, "kab": "Kabupaten Ketapang", "prov": "Kalimantan Barat"},
    "Kecamatan Manis Mata": {"lat": -2.4500, "lon": 111.0200, "kab": "Kabupaten Ketapang", "prov": "Kalimantan Barat"},
    "Kecamatan Sandai": {"lat": -1.2500, "lon": 110.5500, "kab": "Kabupaten Ketapang", "prov": "Kalimantan Barat"},
    "Kecamatan Marau": {"lat": -2.2000, "lon": 110.7500, "kab": "Kabupaten Ketapang", "prov": "Kalimantan Barat"},
    "Kecamatan Hulu Sungai": {"lat": -1.5000, "lon": 110.8000, "kab": "Kabupaten Ketapang", "prov": "Kalimantan Barat"},
    # Kabupaten Sambas
    "Kecamatan Sambas": {"lat": 1.3614, "lon": 109.3012, "kab": "Kabupaten Sambas", "prov": "Kalimantan Barat"},
    "Kecamatan Pemangkat": {"lat": 1.1800, "lon": 108.9700, "kab": "Kabupaten Sambas", "prov": "Kalimantan Barat"},
    "Kecamatan Tebas": {"lat": 1.2800, "lon": 109.2000, "kab": "Kabupaten Sambas", "prov": "Kalimantan Barat"},
    # Kabupaten Sanggau
    "Kecamatan Kapuas": {"lat": 0.1238, "lon": 110.5898, "kab": "Kabupaten Sanggau", "prov": "Kalimantan Barat"},
    "Kecamatan Tayan Hilir": {"lat": -0.0500, "lon": 110.1200, "kab": "Kabupaten Sanggau", "prov": "Kalimantan Barat"},
    # Kabupaten Kapuas Hulu
    "Kecamatan Putussibau Utara": {"lat": 0.8621, "lon": 112.9254, "kab": "Kabupaten Kapuas Hulu", "prov": "Kalimantan Barat"},
    "Kecamatan Putussibau Selatan": {"lat": 0.8200, "lon": 112.9300, "kab": "Kabupaten Kapuas Hulu", "prov": "Kalimantan Barat"},
    # Kabupaten Lain di Kalbar
    "Kecamatan Nanga Pinoh": {"lat": -0.3300, "lon": 111.7500, "kab": "Kabupaten Melawi", "prov": "Kalimantan Barat"},
    "Kecamatan Sekadau Hilir": {"lat": 0.0200, "lon": 110.9500, "kab": "Kabupaten Sekadau", "prov": "Kalimantan Barat"},
    "Kecamatan Ngabang": {"lat": 0.3800, "lon": 109.9500, "kab": "Kabupaten Landak", "prov": "Kalimantan Barat"},
    "Kecamatan Bengkayang": {"lat": 0.8200, "lon": 109.6500, "kab": "Kabupaten Bengkayang", "prov": "Kalimantan Barat"},
    "Kecamatan Sukadana": {"lat": -1.2500, "lon": 109.9500, "kab": "Kabupaten Kayong Utara", "prov": "Kalimantan Barat"},
    "Kecamatan Mempawah Hilir": {"lat": 0.3500, "lon": 108.9600, "kab": "Kabupaten Mempawah", "prov": "Kalimantan Barat"},
    "Kecamatan Sungai Pinyuh": {"lat": 0.2800, "lon": 109.0800, "kab": "Kabupaten Mempawah", "prov": "Kalimantan Barat"},
    "Kecamatan Singkawang Barat": {"lat": 0.9050, "lon": 108.9850, "kab": "Kota Singkawang", "prov": "Kalimantan Barat"},

    # --- Kalimantan Tengah ---
    # Kota Palangka Raya
    "Kecamatan Pahandut": {"lat": -2.2078, "lon": 113.9165, "kab": "Kota Palangka Raya", "prov": "Kalimantan Tengah"},
    "Kecamatan Jekan Raya": {"lat": -2.1850, "lon": 113.8850, "kab": "Kota Palangka Raya", "prov": "Kalimantan Tengah"},
    "Kecamatan Sebangau": {"lat": -2.3500, "lon": 113.9500, "kab": "Kota Palangka Raya", "prov": "Kalimantan Tengah"},
    "Kecamatan Bukit Batu": {"lat": -1.9800, "lon": 113.6200, "kab": "Kota Palangka Raya", "prov": "Kalimantan Tengah"},
    # Kabupaten Kotawaringin Barat
    "Kecamatan Arut Selatan": {"lat": -2.6854, "lon": 111.6214, "kab": "Kabupaten Kotawaringin Barat", "prov": "Kalimantan Tengah"},
    "Kecamatan Kumai": {"lat": -2.7400, "lon": 111.7300, "kab": "Kabupaten Kotawaringin Barat", "prov": "Kalimantan Tengah"},
    "Kecamatan Pangkalan Lada": {"lat": -2.4800, "lon": 111.7500, "kab": "Kabupaten Kotawaringin Barat", "prov": "Kalimantan Tengah"},
    "Kecamatan Kotawaringin Lama": {"lat": -2.4200, "lon": 111.4500, "kab": "Kabupaten Kotawaringin Barat", "prov": "Kalimantan Tengah"},
    "Kecamatan Pangkalan Banteng": {"lat": -2.4500, "lon": 111.9500, "kab": "Kabupaten Kotawaringin Barat", "prov": "Kalimantan Tengah"},
    # Kabupaten Kotawaringin Timur
    "Kecamatan Mentawa Baru Ketapang": {"lat": -2.5312, "lon": 112.9512, "kab": "Kabupaten Kotawaringin Timur", "prov": "Kalimantan Tengah"},
    "Kecamatan Baamang": {"lat": -2.5000, "lon": 112.9400, "kab": "Kabupaten Kotawaringin Timur", "prov": "Kalimantan Tengah"},
    "Kecamatan Mentaya Hilir Selatan": {"lat": -2.9500, "lon": 112.9700, "kab": "Kabupaten Kotawaringin Timur", "prov": "Kalimantan Tengah"},
    "Kecamatan Mentaya Hilir Utara": {"lat": -2.7800, "lon": 112.9200, "kab": "Kabupaten Kotawaringin Timur", "prov": "Kalimantan Tengah"},
    "Kecamatan Parenggean": {"lat": -1.8200, "lon": 112.7800, "kab": "Kabupaten Kotawaringin Timur", "prov": "Kalimantan Tengah"},
    "Kecamatan Cempaga": {"lat": -2.2000, "lon": 112.9000, "kab": "Kabupaten Kotawaringin Timur", "prov": "Kalimantan Tengah"},
    "Kecamatan Antang Kalang": {"lat": -1.4500, "lon": 112.5800, "kab": "Kabupaten Kotawaringin Timur", "prov": "Kalimantan Tengah"},
    "Kecamatan Teluk Sampit": {"lat": -3.0500, "lon": 112.9600, "kab": "Kabupaten Kotawaringin Timur", "prov": "Kalimantan Tengah"},
    # Kabupaten Seruyan
    "Kecamatan Hanau": {"lat": -2.6800, "lon": 112.1800, "kab": "Kabupaten Seruyan", "prov": "Kalimantan Tengah"},
    "Kecamatan Danau Seluluk": {"lat": -2.5500, "lon": 112.1800, "kab": "Kabupaten Seruyan", "prov": "Kalimantan Tengah"},
    "Kecamatan Seruyan Hilir": {"lat": -3.3780, "lon": 112.5512, "kab": "Kabupaten Seruyan", "prov": "Kalimantan Tengah"},
    "Kecamatan Seruyan Hilir Timur": {"lat": -3.2800, "lon": 112.6800, "kab": "Kabupaten Seruyan", "prov": "Kalimantan Tengah"},
    "Kecamatan Danau Sembuluh": {"lat": -2.6512, "lon": 112.3689, "kab": "Kabupaten Seruyan", "prov": "Kalimantan Tengah"},
    "Kecamatan Seruyan Raya": {"lat": -2.8500, "lon": 112.6000, "kab": "Kabupaten Seruyan", "prov": "Kalimantan Tengah"},
    "Kecamatan Seruyan Tengah": {"lat": -1.9500, "lon": 112.2500, "kab": "Kabupaten Seruyan", "prov": "Kalimantan Tengah"},
    "Kecamatan Seruyan Hulu": {"lat": -1.3500, "lon": 112.1000, "kab": "Kabupaten Seruyan", "prov": "Kalimantan Tengah"},
    # Kabupaten Kapuas
    "Kecamatan Selat": {"lat": -3.0112, "lon": 114.3850, "kab": "Kabupaten Kapuas", "prov": "Kalimantan Tengah"},
    "Kecamatan Basarang": {"lat": -3.0512, "lon": 114.3120, "kab": "Kabupaten Kapuas", "prov": "Kalimantan Tengah"},
    "Kecamatan Kapuas Murung": {"lat": -2.8500, "lon": 114.4800, "kab": "Kabupaten Kapuas", "prov": "Kalimantan Tengah"},
    "Kecamatan Timpah": {"lat": -2.1800, "lon": 114.2800, "kab": "Kabupaten Kapuas", "prov": "Kalimantan Tengah"},
    "Kecamatan Mantangai": {"lat": -2.7000, "lon": 114.4000, "kab": "Kabupaten Kapuas", "prov": "Kalimantan Tengah"},
    "Kecamatan Kapuas Tengah": {"lat": -1.7500, "lon": 114.3500, "kab": "Kabupaten Kapuas", "prov": "Kalimantan Tengah"},
    # Kabupaten Pulang Pisau
    "Kecamatan Kahayan Hilir": {"lat": -2.7541, "lon": 114.2514, "kab": "Kabupaten Pulang Pisau", "prov": "Kalimantan Tengah"},
    "Kecamatan Pandih Batu": {"lat": -3.1200, "lon": 114.1500, "kab": "Kabupaten Pulang Pisau", "prov": "Kalimantan Tengah"},
    "Kecamatan Maliku": {"lat": -3.0500, "lon": 114.1500, "kab": "Kabupaten Pulang Pisau", "prov": "Kalimantan Tengah"},
    "Kecamatan Jabiren Raya": {"lat": -2.4500, "lon": 114.1200, "kab": "Kabupaten Pulang Pisau", "prov": "Kalimantan Tengah"},
    "Kecamatan Kahayan Kuala": {"lat": -3.4000, "lon": 113.9000, "kab": "Kabupaten Pulang Pisau", "prov": "Kalimantan Tengah"},
    "Kecamatan Sebangau Kuala": {"lat": -2.8500, "lon": 113.8000, "kab": "Kabupaten Pulang Pisau", "prov": "Kalimantan Tengah"},
    # Kabupaten Katingan
    "Kecamatan Katingan Hilir": {"lat": -1.8950, "lon": 113.3850, "kab": "Kabupaten Katingan", "prov": "Kalimantan Tengah"},
    "Kecamatan Tasik Payawan": {"lat": -2.2500, "lon": 113.3500, "kab": "Kabupaten Katingan", "prov": "Kalimantan Tengah"},
    "Kecamatan Kamipang": {"lat": -2.6000, "lon": 113.3800, "kab": "Kabupaten Katingan", "prov": "Kalimantan Tengah"},
    "Kecamatan Mendawai": {"lat": -2.9500, "lon": 113.3500, "kab": "Kabupaten Katingan", "prov": "Kalimantan Tengah"},
    "Kecamatan Katingan Kuala": {"lat": -3.1500, "lon": 113.4000, "kab": "Kabupaten Katingan", "prov": "Kalimantan Tengah"},
    "Kecamatan Katingan Tengah": {"lat": -1.5500, "lon": 113.1500, "kab": "Kabupaten Katingan", "prov": "Kalimantan Tengah"},
    # Kabupaten Sukamara
    "Kecamatan Sukamara": {"lat": -2.6280, "lon": 111.2370, "kab": "Kabupaten Sukamara", "prov": "Kalimantan Tengah"},
    "Kecamatan Jelai": {"lat": -2.9500, "lon": 110.9200, "kab": "Kabupaten Sukamara", "prov": "Kalimantan Tengah"},
    "Kecamatan Balai Riam": {"lat": -2.2500, "lon": 111.0800, "kab": "Kabupaten Sukamara", "prov": "Kalimantan Tengah"},
    "Kecamatan Pantai Lunci": {"lat": -2.8800, "lon": 111.0500, "kab": "Kabupaten Sukamara", "prov": "Kalimantan Tengah"},
    # Kabupaten Lamandau
    "Kecamatan Bulik": {"lat": -2.1380, "lon": 111.4580, "kab": "Kabupaten Lamandau", "prov": "Kalimantan Tengah"},
    "Kecamatan Delang": {"lat": -1.7500, "lon": 111.0500, "kab": "Kabupaten Lamandau", "prov": "Kalimantan Tengah"},
    "Kecamatan Lamandau": {"lat": -1.8500, "lon": 111.3500, "kab": "Kabupaten Lamandau", "prov": "Kalimantan Tengah"},
    "Kecamatan Sematu Jaya": {"lat": -2.0500, "lon": 111.5500, "kab": "Kabupaten Lamandau", "prov": "Kalimantan Tengah"},
    # Kabupaten Barito & Sekitarnya
    "Kecamatan Dusun Selatan": {"lat": -1.7214, "lon": 114.8512, "kab": "Kabupaten Barito Selatan", "prov": "Kalimantan Tengah"},
    "Kecamatan Dusun Utara": {"lat": -1.3500, "lon": 114.9500, "kab": "Kabupaten Barito Selatan", "prov": "Kalimantan Tengah"},
    "Kecamatan Jenamas": {"lat": -2.3500, "lon": 114.9000, "kab": "Kabupaten Barito Selatan", "prov": "Kalimantan Tengah"},
    "Kecamatan Teweh Tengah": {"lat": -0.9500, "lon": 114.9000, "kab": "Kabupaten Barito Utara", "prov": "Kalimantan Tengah"},
    "Kecamatan Dusun Timur": {"lat": -2.0200, "lon": 115.1500, "kab": "Kabupaten Barito Timur", "prov": "Kalimantan Tengah"},
    "Kecamatan Murung": {"lat": -0.6000, "lon": 114.5800, "kab": "Kabupaten Murung Raya", "prov": "Kalimantan Tengah"},
    "Kecamatan Kurun": {"lat": -1.3300, "lon": 113.8800, "kab": "Kabupaten Gunung Mas", "prov": "Kalimantan Tengah"},

    # --- Kalimantan Selatan ---
    # Kota Banjarmasin & Banjarbaru
    "Kecamatan Banjarmasin Tengah": {"lat": -3.3194, "lon": 114.5908, "kab": "Kota Banjarmasin", "prov": "Kalimantan Selatan"},
    "Kecamatan Banjarmasin Selatan": {"lat": -3.3500, "lon": 114.6000, "kab": "Kota Banjarmasin", "prov": "Kalimantan Selatan"},
    "Kecamatan Banjarbaru Selatan": {"lat": -3.4412, "lon": 114.8312, "kab": "Kota Banjarbaru", "prov": "Kalimantan Selatan"},
    "Kecamatan Landasan Ulin": {"lat": -3.4400, "lon": 114.7500, "kab": "Kota Banjarbaru", "prov": "Kalimantan Selatan"},
    # Kabupaten Banjar
    "Kecamatan Martapura": {"lat": -3.4144, "lon": 114.8500, "kab": "Kabupaten Banjar", "prov": "Kalimantan Selatan"},
    "Kecamatan Gambut": {"lat": -3.4100, "lon": 114.6800, "kab": "Kabupaten Banjar", "prov": "Kalimantan Selatan"},
    "Kecamatan Aluh-Aluh": {"lat": -3.4512, "lon": 114.5812, "kab": "Kabupaten Banjar", "prov": "Kalimantan Selatan"},
    "Kecamatan Simpang Empat": {"lat": -3.1500, "lon": 115.0200, "kab": "Kabupaten Banjar", "prov": "Kalimantan Selatan"},
    # Kabupaten Tanah Laut
    "Kecamatan Pelaihari": {"lat": -3.7954, "lon": 114.7712, "kab": "Kabupaten Tanah Laut", "prov": "Kalimantan Selatan"},
    "Kecamatan Bati-Bati": {"lat": -3.5800, "lon": 114.7200, "kab": "Kabupaten Tanah Laut", "prov": "Kalimantan Selatan"},
    "Kecamatan Jorong": {"lat": -3.8800, "lon": 115.1000, "kab": "Kabupaten Tanah Laut", "prov": "Kalimantan Selatan"},
    "Kecamatan Kintap": {"lat": -3.8200, "lon": 115.2800, "kab": "Kabupaten Tanah Laut", "prov": "Kalimantan Selatan"},
    # Kabupaten Barito Kuala
    "Kecamatan Marabahan": {"lat": -2.9800, "lon": 114.7500, "kab": "Kabupaten Barito Kuala", "prov": "Kalimantan Selatan"},
    "Kecamatan Alalak": {"lat": -3.2500, "lon": 114.6000, "kab": "Kabupaten Barito Kuala", "prov": "Kalimantan Selatan"},
    "Kecamatan Mandastana": {"lat": -3.1800, "lon": 114.6500, "kab": "Kabupaten Barito Kuala", "prov": "Kalimantan Selatan"},
    # Kabupaten Tapin
    "Kecamatan Tapin Utara": {"lat": -2.9200, "lon": 115.1500, "kab": "Kabupaten Tapin", "prov": "Kalimantan Selatan"},
    "Kecamatan Binuang": {"lat": -3.1200, "lon": 115.1500, "kab": "Kabupaten Tapin", "prov": "Kalimantan Selatan"},
    "Kecamatan Candi Laras Selatan": {"lat": -2.8000, "lon": 114.9500, "kab": "Kabupaten Tapin", "prov": "Kalimantan Selatan"},
    "Kecamatan Candi Laras Utara": {"lat": -2.6200, "lon": 114.8800, "kab": "Kabupaten Tapin", "prov": "Kalimantan Selatan"},
    # Kabupaten Hulu Sungai & Tabalong
    "Kecamatan Kandangan": {"lat": -2.7800, "lon": 115.2500, "kab": "Kabupaten Hulu Sungai Selatan", "prov": "Kalimantan Selatan"},
    "Kecamatan Barabai": {"lat": -2.5800, "lon": 115.3800, "kab": "Kabupaten Hulu Sungai Tengah", "prov": "Kalimantan Selatan"},
    "Kecamatan Amuntai Tengah": {"lat": -2.4200, "lon": 115.2500, "kab": "Kabupaten Hulu Sungai Utara", "prov": "Kalimantan Selatan"},
    "Kecamatan Murung Pudak": {"lat": -2.1600, "lon": 115.4200, "kab": "Kabupaten Tabalong", "prov": "Kalimantan Selatan"},
    "Kecamatan Kelua": {"lat": -2.2800, "lon": 115.3200, "kab": "Kabupaten Tabalong", "prov": "Kalimantan Selatan"},
    "Kecamatan Muara Uya": {"lat": -1.7500, "lon": 115.5800, "kab": "Kabupaten Tabalong", "prov": "Kalimantan Selatan"},
    "Kecamatan Paringin": {"lat": -2.3500, "lon": 115.5000, "kab": "Kabupaten Balangan", "prov": "Kalimantan Selatan"},
    # Kabupaten Tanah Bumbu
    "Kecamatan Batulicin": {"lat": -3.4500, "lon": 116.0000, "kab": "Kabupaten Tanah Bumbu", "prov": "Kalimantan Selatan"},
    "Kecamatan Satui": {"lat": -3.7800, "lon": 115.3500, "kab": "Kabupaten Tanah Bumbu", "prov": "Kalimantan Selatan"},
    "Kecamatan Kusan Hilir": {"lat": -3.5800, "lon": 115.8500, "kab": "Kabupaten Tanah Bumbu", "prov": "Kalimantan Selatan"},
    "Kecamatan Mantewe": {"lat": -3.2000, "lon": 115.6500, "kab": "Kabupaten Tanah Bumbu", "prov": "Kalimantan Selatan"},
    # Kabupaten Kotabaru
    "Kecamatan Pulau Laut Utara": {"lat": -3.2954, "lon": 116.2214, "kab": "Kabupaten Kotabaru", "prov": "Kalimantan Selatan"},
    "Kecamatan Kelumpang Hilir": {"lat": -3.0500, "lon": 116.0500, "kab": "Kabupaten Kotabaru", "prov": "Kalimantan Selatan"},
    "Kecamatan Kelumpang Hulu": {"lat": -2.7000, "lon": 115.9500, "kab": "Kabupaten Kotabaru", "prov": "Kalimantan Selatan"},
    "Kecamatan Pamukan Utara": {"lat": -2.3800, "lon": 116.1200, "kab": "Kabupaten Kotabaru", "prov": "Kalimantan Selatan"},
    "Kecamatan Pulau Laut Selatan": {"lat": -3.8500, "lon": 116.1500, "kab": "Kabupaten Kotabaru", "prov": "Kalimantan Selatan"},

    # --- Kalimantan Timur ---
    # Kota Samarinda, Balikpapan, Bontang
    "Kecamatan Samarinda Kota": {"lat": -0.5022, "lon": 117.1536, "kab": "Kota Samarinda", "prov": "Kalimantan Timur"},
    "Kecamatan Balikpapan Kota": {"lat": -1.2654, "lon": 116.8312, "kab": "Kota Balikpapan", "prov": "Kalimantan Timur"},
    "Kecamatan Bontang Utara": {"lat": 0.1350, "lon": 117.4850, "kab": "Kota Bontang", "prov": "Kalimantan Timur"},
    # Kabupaten Kutai Kartanegara
    "Kecamatan Tenggarong": {"lat": -0.4215, "lon": 116.9854, "kab": "Kabupaten Kutai Kartanegara", "prov": "Kalimantan Timur"},
    "Kecamatan Samboja": {"lat": -1.0200, "lon": 117.0500, "kab": "Kabupaten Kutai Kartanegara", "prov": "Kalimantan Timur"},
    "Kecamatan Muara Badak": {"lat": -0.3200, "lon": 117.3800, "kab": "Kabupaten Kutai Kartanegara", "prov": "Kalimantan Timur"},
    "Kecamatan Loa Janan": {"lat": -0.6000, "lon": 117.0800, "kab": "Kabupaten Kutai Kartanegara", "prov": "Kalimantan Timur"},
    "Kecamatan Kota Bangun": {"lat": -0.2500, "lon": 116.5800, "kab": "Kabupaten Kutai Kartanegara", "prov": "Kalimantan Timur"},
    "Kecamatan Marang Kayu": {"lat": 0.0200, "lon": 117.3500, "kab": "Kabupaten Kutai Kartanegara", "prov": "Kalimantan Timur"},
    # Kabupaten Penajam Paser Utara
    "Kecamatan Penajam": {"lat": -1.2800, "lon": 116.7500, "kab": "Kabupaten Penajam Paser Utara", "prov": "Kalimantan Timur"},
    "Kecamatan Sepaku": {"lat": -0.9200, "lon": 116.8500, "kab": "Kabupaten Penajam Paser Utara", "prov": "Kalimantan Timur"},
    "Kecamatan Waru": {"lat": -1.3800, "lon": 116.6000, "kab": "Kabupaten Penajam Paser Utara", "prov": "Kalimantan Timur"},
    # Kabupaten Paser
    "Kecamatan Tanah Grogot": {"lat": -1.9054, "lon": 116.2014, "kab": "Kabupaten Paser", "prov": "Kalimantan Timur"},
    "Kecamatan Kuaro": {"lat": -1.8200, "lon": 116.0800, "kab": "Kabupaten Paser", "prov": "Kalimantan Timur"},
    "Kecamatan Batu Sopang": {"lat": -1.9500, "lon": 115.8500, "kab": "Kabupaten Paser", "prov": "Kalimantan Timur"},
    "Kecamatan Long Ikis": {"lat": -1.5500, "lon": 116.1500, "kab": "Kabupaten Paser", "prov": "Kalimantan Timur"},
    "Kecamatan Long Kali": {"lat": -1.4200, "lon": 116.2500, "kab": "Kabupaten Paser", "prov": "Kalimantan Timur"},
    # Kabupaten Kutai Timur
    "Kecamatan Sangatta Utara": {"lat": 0.4950, "lon": 117.5512, "kab": "Kabupaten Kutai Timur", "prov": "Kalimantan Timur"},
    "Kecamatan Bengalon": {"lat": 0.7500, "lon": 117.6200, "kab": "Kabupaten Kutai Timur", "prov": "Kalimantan Timur"},
    "Kecamatan Kaliorang": {"lat": 0.8500, "lon": 117.7500, "kab": "Kabupaten Kutai Timur", "prov": "Kalimantan Timur"},
    "Kecamatan Sangkulirang": {"lat": 1.0200, "lon": 117.9500, "kab": "Kabupaten Kutai Timur", "prov": "Kalimantan Timur"},
    "Kecamatan Muara Wahau": {"lat": 1.2500, "lon": 116.9200, "kab": "Kabupaten Kutai Timur", "prov": "Kalimantan Timur"},
    # Kabupaten Berau
    "Kecamatan Tanjung Redeb": {"lat": 2.1524, "lon": 117.4912, "kab": "Kabupaten Berau", "prov": "Kalimantan Timur"},
    "Kecamatan Sambaliung": {"lat": 2.1200, "lon": 117.5200, "kab": "Kabupaten Berau", "prov": "Kalimantan Timur"},
    # Kabupaten Kutai Barat
    "Kecamatan Barong Tongkok": {"lat": -0.2300, "lon": 115.7000, "kab": "Kabupaten Kutai Barat", "prov": "Kalimantan Timur"},
    "Kecamatan Melak": {"lat": -0.2200, "lon": 115.8500, "kab": "Kabupaten Kutai Barat", "prov": "Kalimantan Timur"},
    "Kecamatan Jempang": {"lat": -0.5500, "lon": 116.2500, "kab": "Kabupaten Kutai Barat", "prov": "Kalimantan Timur"},
    "Kecamatan Ujoh Bilang": {"lat": 0.1500, "lon": 115.3500, "kab": "Kabupaten Mahakam Hulu", "prov": "Kalimantan Timur"},

    # --- Kalimantan Utara ---
    # Kota Tarakan
    "Kecamatan Tarakan Tengah": {"lat": 3.3270, "lon": 117.5965, "kab": "Kota Tarakan", "prov": "Kalimantan Utara"},
    # Kabupaten Bulungan
    "Kecamatan Tanjung Selor": {"lat": 2.9041, "lon": 117.3643, "kab": "Kabupaten Bulungan", "prov": "Kalimantan Utara"},
    "Kecamatan Tanjung Palas": {"lat": 2.8800, "lon": 117.3200, "kab": "Kabupaten Bulungan", "prov": "Kalimantan Utara"},
    "Kecamatan Sekatak": {"lat": 3.2500, "lon": 117.0500, "kab": "Kabupaten Bulungan", "prov": "Kalimantan Utara"},
    # Kabupaten Nunukan & Malinau
    "Kecamatan Nunukan": {"lat": 4.1357, "lon": 117.6467, "kab": "Kabupaten Nunukan", "prov": "Kalimantan Utara"},
    "Kecamatan Malinau Kota": {"lat": 3.5843, "lon": 116.6388, "kab": "Kabupaten Malinau", "prov": "Kalimantan Utara"},
    "Kecamatan Sesayap": {"lat": 3.5500, "lon": 117.2500, "kab": "Kabupaten Tana Tidung", "prov": "Kalimantan Utara"},
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
        kecamatan = kec_in_kab if kec_in_kab_d <= 70.0 else ""
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
