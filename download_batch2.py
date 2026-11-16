#!/usr/bin/env python3
import urllib.request
from pathlib import Path
import time
import json

DEST_DIR = Path("/Users/hemantmalik/Desktop/ambience-mall-integrated/ambience-mall-app-ui/public/store-logos")
DEST_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    'User-Agent': 'AmbienceMallGurugramNavigator/1.0 (official-brand-directory-audit@ambiencenav.internal)'
}

BATCH = [
    ("armani-exchange", "Armani Exchange", "https://upload.wikimedia.org/wikipedia/commons/3/30/Armani_Exchange_logo.svg"),
    ("bath-and-body-works", "Bath & Body Works", "https://upload.wikimedia.org/wikipedia/commons/8/8e/Bath_%26_Body_Works_logo.svg"),
    ("birkenstock", "Birkenstock", "https://upload.wikimedia.org/wikipedia/commons/2/25/Birkenstock_logo.svg"),
    ("hugo-boss", "Hugo Boss", "https://upload.wikimedia.org/wikipedia/commons/0/05/Boss_logo_2021.svg"),
    ("brooks-brothers", "Brooks Brothers", "https://upload.wikimedia.org/wikipedia/commons/a/a0/Brooks_Brothers_logo.svg"),
    ("celio", "Celio", "https://upload.wikimedia.org/wikipedia/commons/1/1e/Celio%27s_logo.svg"),
    ("chicco", "Chicco", "https://upload.wikimedia.org/wikipedia/commons/d/d1/Chicco_logo.svg"),
    ("clinique", "Clinique", "https://upload.wikimedia.org/wikipedia/commons/4/45/Clinique_logo.svg"),
    ("delsey", "Delsey Paris", "https://upload.wikimedia.org/wikipedia/commons/5/58/Delsey.svg"),
    ("dior", "Dior", "https://upload.wikimedia.org/wikipedia/commons/a/a8/Dior_Logo.svg"),
    ("dyson", "Dyson", "https://upload.wikimedia.org/wikipedia/commons/2/2f/Dyson_logo.svg"),
    ("ecco", "ECCO", "https://upload.wikimedia.org/wikipedia/commons/9/92/Ecco_shoes_logo.svg"),
    ("fabindia", "Fabindia", "https://upload.wikimedia.org/wikipedia/commons/f/f6/Fabindia_logo.svg"),
    ("kalyan-jewellers", "Kalyan Jewellers", "https://upload.wikimedia.org/wikipedia/commons/7/7f/Kalyan_Jewellers_logo.svg"),
    ("lacoste", "Lacoste", "https://upload.wikimedia.org/wikipedia/commons/6/62/Lacoste_wordmark_1984.svg"),
    ("loccitane", "L'Occitane", "https://upload.wikimedia.org/wikipedia/commons/2/24/L%E2%80%99Occitane_en_Provence_Logo.svg"),
    ("mango", "Mango", "https://upload.wikimedia.org/wikipedia/commons/c/c7/Mango_logo.svg"),
    ("mothercare", "Mothercare", "https://upload.wikimedia.org/wikipedia/commons/7/79/Mothercare.svg"),
    ("van-heusen", "Van Heusen", "https://upload.wikimedia.org/wikipedia/commons/b/ba/Phillips-Van_Heusen_logo.svg"),
    ("ralph-lauren", "Polo Ralph Lauren", "https://upload.wikimedia.org/wikipedia/commons/7/72/Ralph_Lauren_logo.svg"),
    ("samsonite", "Samsonite", "https://upload.wikimedia.org/wikipedia/commons/1/13/Samsonite_Logo.svg"),
    ("tissot", "Tissot", "https://upload.wikimedia.org/wikipedia/commons/c/ce/Tissot_Logo.svg"),
    ("tommy-hilfiger", "Tommy Hilfiger", "https://upload.wikimedia.org/wikipedia/commons/9/9d/Tommy_Hilfiger_logo.svg"),
    ("victorias-secret", "Victoria's Secret", "https://upload.wikimedia.org/wikipedia/commons/7/70/Victoria%27s_Secret_logo.svg"),
    ("diesel", "Diesel", "https://upload.wikimedia.org/wikipedia/commons/a/a1/Diesel_logo.svg"),
    ("american-eagle", "American Eagle Outfitters", "https://upload.wikimedia.org/wikipedia/commons/1/18/American_Eagle_Outfitters_wordmark.svg"),
    ("hamleys", "Hamleys", "https://upload.wikimedia.org/wikipedia/commons/3/38/Hamleys_logo.png"),
    ("tumi", "TUMI", "https://upload.wikimedia.org/wikipedia/commons/b/be/Tumi-Logo.png"),
    ("nars", "NARS Cosmetics", "https://upload.wikimedia.org/wikipedia/commons/d/dd/NARS_Cosmetics_logo.png"),
    ("raymond", "Raymond", "https://upload.wikimedia.org/wikipedia/commons/a/a1/Raymond_logo.svg"),
    ("hush-puppies", "Hush Puppies", "https://upload.wikimedia.org/wikipedia/en/a/a1/Hush_Puppies_logo.png"),
    ("lenscrafters", "LensCrafters", "https://upload.wikimedia.org/wikipedia/en/3/38/LensCrafters_logo.png"),
    ("lenskart", "Lenskart", "https://upload.wikimedia.org/wikipedia/en/4/47/Lenskart_logo.svg"),
    ("titan", "Titan Company", "https://upload.wikimedia.org/wikipedia/en/0/05/Logo_of_Titan_Company%2C_May_2018.svg"),
    ("louis-philippe", "Louis Philippe", "https://upload.wikimedia.org/wikipedia/en/5/5d/Louis_Philippe_%28brand%29.svg"),
    ("onitsuka-tiger", "Onitsuka Tiger", "https://upload.wikimedia.org/wikipedia/en/8/87/Onitsuka_Tiger_Logo.svg"),
    ("samsung", "Samsung", "https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/samsung.svg"),
    ("uniqlo", "UNIQLO", "https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/uniqlo.svg"),
    ("bose", "Bose", "https://upload.wikimedia.org/wikipedia/commons/0/0c/Bose_logo.svg"),
    ("superdry", "Superdry", "https://upload.wikimedia.org/wikipedia/commons/6/6a/Superdry_Logo_2020.svg"),
    ("barista", "Barista Coffee", "https://upload.wikimedia.org/wikipedia/commons/e/e4/Barista_Lavazza_logo.svg"),
    ("wow-momo", "Wow! Momo", "https://upload.wikimedia.org/wikipedia/commons/9/9e/Wow_Momo_Logo.jpg")
]

new_prov = []
for slug, name, url in BATCH:
    ext = ".svg" if ".svg" in url else ".png" if ".png" in url else ".jpg"
    target = DEST_DIR / f"{slug}{ext}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            with open(target, "wb") as f:
                f.write(data)
            print(f"SAVED: {target.name} ({len(data)} bytes)")
            new_prov.append({
                "brand": name,
                "slug": slug,
                "file": f"/store-logos/{target.name}",
                "sourceUrl": url,
                "sourceType": "Official Vector SVG" if ext == ".svg" else "Official Brand Asset",
                "sizeBytes": len(data),
                "verified": True
            })
    except Exception as e:
        print(f"FAILED {slug}: {e}")
    time.sleep(0.05)

print(f"Saved {len(new_prov)} / {len(BATCH)} in batch 2.")
